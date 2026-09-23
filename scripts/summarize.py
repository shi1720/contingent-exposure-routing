"""Uncertainty intervals respect independent networks or paired API tasks."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def interval(values,seed=20260923):
    x=np.asarray(values,float);rng=np.random.default_rng(seed)
    means=x[rng.integers(len(x),size=(2000,len(x)))].mean(axis=1)
    return [float(x.mean()),*map(float,np.quantile(means,[.025,.975]))]

def ratio_interval(base,method,seed=20260924):
    base,method=np.asarray(base),np.asarray(method);rng=np.random.default_rng(seed)
    ix=rng.integers(len(base),size=(2000,len(base)))
    values=1-method[ix].mean(axis=1)/base[ix].mean(axis=1)
    return [float(1-method.mean()/base.mean()),*map(float,np.quantile(values,[.025,.975]))]

def main():
    x=pd.read_csv(ROOT/'results/synthetic.csv'); x['gain']=1-x.cer/x['count'];x['gap']=x.cer/x.lower_bound-1
    syn=[]
    for (feedback,corr,r),g in x.groupby(['feedback','correlation','outage_size']):
        per=g.groupby('network').gain.mean()
        syn.append(dict(feedback=feedback,correlation=corr,outage_size=int(r),
                        gain=interval(per),mean_relaxation_gap=float(g.gap.mean()) if g.gap.notna().any() else None))
    losses=pd.read_csv(ROOT/'results/api-task-losses.csv.gz')
    api=[]
    for r in [1,2,0]:
        g=losses if r==0 else losses[losses.outage_size==r]
        per=g.groupby('task_id')[['count','cer','diagonal','equal','robust','common']].mean()
        for method in ['cer','diagonal','equal','robust','common']:
            api.append(dict(outage_size=r,method=method,gain=ratio_interval(per['count'],per[method]),
                            mean_risk=float(per[method].mean()),count_risk=float(per['count'].mean())))
    rounding=pd.read_csv(ROOT/'results/rounding.csv')
    rnd=[]
    for n,g in rounding.groupby('n'):
        rnd.append(dict(n=int(n),independent_premium=float((g.independent/g.fractional-1).mean()),
                        rounded_gap=float((g.rounded/g.fractional-1).mean()),
                        max_certificate_violation=float((g.rounded-g.certificate).max())))
    stats=dict(synthetic=syn,api=api,rounding=rnd,
               swaps_median_runtime_ms=float(x.runtime_seconds.median()*1000),
               max_solver_residual=float(x.solver_residual.max()),
               maximum_observed_gain=float(x.gain.max()))
    (ROOT/'results/summary.json').write_text(json.dumps(stats,indent=2)+'\n')
    print(json.dumps({k:stats[k] for k in ['api','rounding']},indent=2))

if __name__=='__main__': main()
