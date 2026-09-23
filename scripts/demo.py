"""Offline executable demonstration: no API key, trading, or market connection."""
import argparse,json
from pathlib import Path
import numpy as np
from cer.networks import make_network
from cer.risk import one_hot,risk
from cer.routing import count_balanced,quota_swaps,eligibility,fractional_optimum

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seed',type=int,default=1721406)
    ap.add_argument('--outage',type=int,nargs='+',default=[0,1])
    ap.add_argument('--output',type=Path)
    args=ap.parse_args();k=6
    outage=set(args.outage)
    if not outage or not outage<set(range(k)):ap.error('Choose a nonempty proper subset of endpoints 0 through 5')
    net=make_network(args.seed);A,p=net['A'],net['primary'];S=np.eye(k)
    survivors=sorted(set(range(k))-outage)
    baseline,free=count_balanced(p,survivors,np.random.default_rng(8))
    routed,history=quota_swaps(A,S,baseline,free)
    quotas=np.bincount(baseline,minlength=k)
    _,lower,residual=fractional_optimum(A,S,eligibility(p,survivors),quotas)
    before,after=risk(A,one_hot(baseline,k),S),risk(A,one_hot(routed,k),S)
    result=dict(seed=args.seed,outage=sorted(outage),count_risk=before,cer_risk=after,
                relative_reduction=1-after/before,numerical_lower_bound=lower,
                relative_gap_to_bound=after/lower-1,solver_residual=residual,
                endpoint_counts=quotas.tolist(),swaps=len(history)-1,
                routes=[dict(institution=i,primary=int(p[i]),baseline=int(baseline[i]),cer=int(routed[i])) for i in range(len(p))],
                units='normalized squared price displacement; synthetic network')
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items() if key!='routes'},indent=2))

if __name__=='__main__':main()
