"""Run deterministic risk evaluation over all declared synthetic scenarios."""
import itertools,json,time
from pathlib import Path
import numpy as np
import pandas as pd
from cer.networks import make_network
from cer.risk import risk,one_hot,random_routing_risk
from cer.routing import eligibility,count_balanced,quota_swaps,fractional_optimum,conditional_round

ROOT=Path(__file__).resolve().parents[1]


def main():
    protocol=json.loads((ROOT/'config/protocol.json').read_text())
    k=protocol['synthetic_providers']; records=[]; start=time.perf_counter()
    for network in range(protocol['network_instances']):
        for feedback in protocol['feedback_radii']:
            net=make_network(protocol['seed']+1000+network,feedback=feedback)
            A,primary=net['A'],net['primary']
            for r in protocol['outage_sizes']:
                for outage in itertools.combinations(range(k),r):
                    survivors=[j for j in range(k) if j not in outage]
                    seed=protocol['seed']+100000+network*100+sum(2**j for j in outage)
                    balanced,free=count_balanced(primary,survivors,np.random.default_rng(seed))
                    t=time.perf_counter(); optimized,hist=quota_swaps(A,np.eye(k),balanced,free)
                    runtime=time.perf_counter()-t
                    common=primary.copy(); common[free]=survivors[0]
                    quota=np.bincount(balanced,minlength=k)
                    lower,residual=float('nan'),float('nan')
                    if feedback==.4:
                        _,lower,residual=fractional_optimum(A,np.eye(k),eligibility(primary,survivors),quota)
                    for corr in protocol['provider_correlations']:
                        S=(1-corr)*np.eye(k)+corr*np.ones((k,k))
                        row=dict(network=network,feedback=feedback,correlation=corr,outage_size=r,
                                 outage=','.join(map(str,outage)),normal=risk(A,one_hot(primary,k),S),
                                 common=risk(A,one_hot(common,k),S),count=risk(A,one_hot(balanced,k),S),
                                 cer=risk(A,one_hot(optimized,k),S),runtime_seconds=runtime,
                                 swaps=len(hist)-1,quota_verified=bool(np.array_equal(np.bincount(optimized,minlength=k),quota)),
                                 lower_bound=(1-corr)*lower+corr*np.sum(A.sum(axis=1)**2) if np.isfinite(lower) else lower,
                                 solver_residual=residual)
                        records.append(row)
        if (network+1)%10==0: print(f'Networks {network+1}/{protocol["network_instances"]}; elapsed {time.perf_counter()-start:.1f}s',flush=True)
    df=pd.DataFrame(records); df.to_csv(ROOT/'results/synthetic.csv',index=False)
    # Uniform-exposure control: identical quotas imply identical exposure risk.
    controls=[]
    for feedback in protocol['feedback_radii']:
        net=make_network(100,feedback=feedback,homogeneous=True)
        for r in [1,2]:
            base,free=count_balanced(net['primary'],list(range(r,k)),np.random.default_rng(5))
            opt,_=quota_swaps(net['A'],np.eye(k),base,free)
            controls.append(dict(feedback=feedback,outage_size=r,count=risk(net['A'],one_hot(base,k),np.eye(k)),cer=risk(net['A'],one_hot(opt,k),np.eye(k))))
    pd.DataFrame(controls).to_csv(ROOT/'results/homogeneous-controls.csv',index=False)
    # Exact finite-agent premium; the oracle risk itself does not need Monte Carlo.
    rounding=[]
    for n in [4,8,16,32,64]:
        for seed in range(20):
            net=make_network(30000+seed,n=n,providers=4)
            A=net['A']; S=np.eye(4); allowed=np.ones((n,4),bool)
            Q,lower,residual=fractional_optimum(A,S,allowed)
            z,history=conditional_round(A,Q,S,allowed)
            rounding.append(dict(n=n,seed=seed,fractional=lower,independent=random_routing_risk(A,Q,S),
                                 rounded=risk(A,one_hot(z,4),S),certificate=history[0],
                                 effective_n=float(np.sum(A.sum(axis=1)**2)/np.sum(A**2)),solver_residual=residual))
    pd.DataFrame(rounding).to_csv(ROOT/'results/rounding.csv',index=False)
    info=dict(rows=len(df),networks=protocol['network_instances'],all_quotas_preserved=bool(df.quota_verified.all()),
              max_solver_residual=float(df.solver_residual.max()),runtime_seconds=time.perf_counter()-start)
    (ROOT/'results/synthetic-run.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(info,indent=2))

if __name__=='__main__': main()
