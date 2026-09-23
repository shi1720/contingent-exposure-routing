import numpy as np
from .risk import exposure_map


def make_network(seed, n=48, assets=6, providers=6, feedback=.4, homogeneous=False):
    rng=np.random.default_rng(seed)
    size=np.ones(n) if homogeneous else rng.lognormal(0,1.1,n)
    size/=size.sum()
    H=np.full((assets,n),1/assets) if homogeneous else rng.dirichlet(np.full(assets,.35),size=n).T
    impact=np.ones(assets) if homogeneous else rng.lognormal(0,.5,assets)
    impact/=impact.mean()
    A,B,E=exposure_map(H,size,impact,feedback)
    primary=np.arange(n)%providers
    rng.shuffle(primary)
    return dict(A=A,B=B,E=E,H=H,size=size,impact=impact,primary=primary)
