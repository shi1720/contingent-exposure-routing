"""Fit on calibration tasks; replay fixed policies on paired held-out tasks."""
import itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
from cer.networks import make_network
from cer.risk import one_hot,risk
from cer.routing import count_balanced,quota_swaps

ROOT=Path(__file__).resolve().parents[1]

def main():
    protocol=json.loads((ROOT/'config/protocol.json').read_text())
    models=protocol['models']; k=len(models)
    tasks=[json.loads(x) for x in (ROOT/'data/raw/tasks.jsonl').read_text().splitlines()]
    raw=[json.loads(x) for x in (ROOT/'data/raw/api-responses.jsonl').read_text().splitlines()]
    records={(r['task_id'],r['requested_model']):r for r in raw}
    assert len(records)==len(raw)==len(tasks)*k, 'Collection must be complete, with no duplicate jobs'
    E=np.array([[(records[t['id'],m]['trade_dollars']-float(t['exact_trade']))/t['nav'] for m in models] for t in tasks])
    cal=np.array([t['split']=='calibration' for t in tasks]); test=~cal
    S=E[cal].T@E[cal]/cal.sum()
    np.savez_compressed(ROOT/'data/processed/error-moments.npz',errors=E,calibration=cal,second_moment=S,models=np.array(models))
    summaries=[]
    for j,m in enumerate(models):
        for name,mask in [('calibration',cal),('test',test),('all',np.ones(len(tasks),bool))]:
            rr=[records[t['id'],m] for t,use in zip(tasks,mask) if use]
            e=E[mask,j]
            summaries.append(dict(model=m,split=name,n=len(rr),valid=sum(r['valid'] for r in rr),
                                  rmse_bps=1e4*np.sqrt(np.mean(e**2)),mae_bps=1e4*np.mean(abs(e)),
                                  mean_bps=1e4*np.mean(e),within_one_bp=int(np.sum(abs(e)<=1e-4)),
                                  estimated_cost_usd=sum(r['estimated_cost_usd'] for r in rr),
                                  input_tokens=sum(r['usage'].get('prompt_tokens',0) for r in rr),
                                  output_tokens=sum(r['usage'].get('completion_tokens',0) for r in rr)))
    pd.DataFrame(summaries).to_csv(ROOT/'results/api-models.csv',index=False)
    policies=[]; all_losses=[]; traces=[]
    test_ids=np.array([t['id'] for t in tasks])[test]
    for network in range(protocol['network_instances']):
        net=make_network(protocol['seed']+1000+network,providers=k,feedback=.4)
        A,primary=net['A'],net['primary']
        for r in [1,2]:
            for outage in itertools.combinations(range(k),r):
                survivors=[j for j in range(k) if j not in outage]
                base,free=count_balanced(primary,survivors,np.random.default_rng(protocol['seed']+200000+100*network+sum(2**j for j in outage)))
                opt,_=quota_swaps(A,S,base,free)
                diagonal,_=quota_swaps(A,np.diag(np.diag(S)),base,free)
                equal,_=quota_swaps(A,np.eye(k),base,free)
                robust,_=quota_swaps(A,S+.1*np.trace(S)/k*np.eye(k),base,free)
                best=min(survivors,key=lambda j:S[j,j]); common=primary.copy(); common[free]=best
                zdict={'count':base,'cer':opt,'diagonal':diagonal,'equal':equal,'robust':robust,'common':common}
                losses={}
                for name,z in zdict.items():
                    price=E[test]@(A@one_hot(z,k)).T
                    losses[name]=np.sum(price**2,axis=1)
                policy=dict(network=network,outage_size=r,outage=','.join(map(str,outage)))
                policy.update({name:float(value.mean()) for name,value in losses.items()})
                policies.append(policy)
                for t in range(test.sum()):
                    all_losses.append(dict(network=network,outage_size=r,outage=','.join(map(str,outage)),task_id=test_ids[t],**{name:float(value[t]) for name,value in losses.items()}))
                if network==0:
                    traces.append(dict(network=network,outage=list(outage),primary=primary.tolist(),**{name:z.tolist() for name,z in zdict.items()}))
    pd.DataFrame(policies).to_csv(ROOT/'results/api-policy-risk.csv',index=False)
    pd.DataFrame(all_losses).to_csv(ROOT/'results/api-task-losses.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    (ROOT/'results/example-routes.json').write_text(json.dumps(traces,indent=2)+'\n')
    info=dict(observations=len(raw),requests=sum(r['attempts'] for r in raw),tasks=len(tasks),test_tasks=int(test.sum()),
              estimated_cost_usd=sum(r['estimated_cost_usd'] for r in raw),
              invalid=sum(not r['valid'] for r in raw),
              first_call=min(r['started_utc'] for r in raw),last_call=max(r['started_utc'] for r in raw),
              calibration_cosine_second_moment=(S/np.sqrt(np.outer(np.diag(S),np.diag(S)))).tolist(),
              protocol_note='Primary: unregularized calibration second moment. Diagonal, equal-variance and 0.1-trace ridge comparisons are secondary diagnostics specified after collection, before policy evaluation.')
    (ROOT/'results/api-run.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(info,indent=2))

if __name__=='__main__':main()
