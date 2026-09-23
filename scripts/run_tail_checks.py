"""Secondary Monte Carlo distribution checks, not market crash forecasts."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from cer.networks import make_network
from cer.routing import count_balanced,quota_swaps
from cer.risk import one_hot,risk,psd_sqrt

ROOT=Path(__file__).resolve().parents[1]

def main():
    n_draws=100000; k=6; rows=[]
    rng=np.random.default_rng(8172406)
    net=make_network(1721406,providers=k,feedback=.4)
    A,primary=net['A'],net['primary']
    base,free=count_balanced(primary,[2,3,4,5],np.random.default_rng(8))
    opt,_=quota_swaps(A,np.eye(k),base,free)
    common=primary.copy();common[free]=2
    for corr in [0.,.3,.8]:
        S=(1-corr)*np.eye(k)+corr*np.ones((k,k))
        normal=rng.normal(size=(n_draws,k))@psd_sqrt(S)
        student=normal/np.sqrt(rng.chisquare(5,size=n_draws)[:,None]/3)
        for dist,epsilon in [('normal',normal),('student_t5',student)]:
            for name,z in [('count',base),('cer',opt),('common',common)]:
                price=epsilon@(A@one_hot(z,k)).T
                quadratic=np.sum(price**2,axis=1)
                # Mean absolute asset price displacement. Explicit normalized units.
                absolute=np.abs(price.mean(axis=1))
                quantile=np.quantile(absolute,.975)
                rows.append(dict(correlation=corr,distribution=dist,method=name,draws=n_draws,
                                 theory=risk(A,one_hot(z,k),S),mc_mean=float(quadratic.mean()),
                                 mc_standard_error=float(quadratic.std(ddof=1)/np.sqrt(n_draws)),
                                 absolute_var975=float(quantile),absolute_es975=float(absolute[absolute>=quantile].mean())))
    pd.DataFrame(rows).to_csv(ROOT/'results/tail-checks.csv',index=False)

if __name__=='__main__':main()
