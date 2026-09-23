import itertools
from decimal import Decimal
import numpy as np
import pytest
from cer.risk import risk, random_routing_risk, routing_premium, one_hot, exposure_map, waterfill
from cer.routing import fractional_optimum, conditional_round, quota_swaps
from cer.tasks import generate_tasks, exact_trade, parse_trade


@pytest.mark.parametrize("seed",range(12))
def test_random_routing_against_exhaustive_assignment(seed):
    rng = np.random.default_rng(seed)
    # Signed exposures and correlated, biased-error second moments allowed.
    A = rng.normal(size=(3,4))
    V = rng.normal(size=(3,3)); S = V@V.T
    Q = rng.dirichlet(np.ones(3),size=4)
    total = 0.
    for z in itertools.product(range(3),repeat=4):
        probability = np.prod([Q[i,j] for i,j in enumerate(z)])
        errors = []
        # Independent implementation via explicit pairwise sum.
        value = sum(np.dot(A[:,i],A[:,j])*S[z[i],z[j]] for i in range(4) for j in range(4))
        total += probability*value
    assert np.isclose(total,random_routing_risk(A,Q,S),rtol=1e-12,atol=1e-12)
    assert routing_premium(A,Q,S) >= -1e-12


@pytest.mark.parametrize("k",[2,3,4,8,16])
def test_symmetric_outage_formula(k):
    for r in range(1,k):
        loads = np.full(k-r,1/k); loads[0] += r/k
        assert np.isclose(loads@loads,(k+r*(r+1))/k**2)
        equal = waterfill(np.full(k-r,1/k),r/k)
        assert np.allclose(equal,1/(k-r))
        assert np.isclose(equal@equal,1/(k-r))


@pytest.mark.parametrize("seed",range(10))
def test_rounding_certificate_and_lower_bound(seed):
    rng=np.random.default_rng(seed)
    A=rng.normal(size=(3,6)); V=rng.normal(size=(3,3)); S=V@V.T
    allowed=np.ones((6,3),bool); allowed[0]=[1,0,0]
    Q,lower,residual=fractional_optimum(A,S,allowed)
    z,history=conditional_round(A,Q,S,allowed)
    exact=min(risk(A,one_hot(z0,3),S) for z0 in itertools.product(range(3),repeat=6) if z0[0]==0)
    assert lower <= exact+1e-6
    assert residual < 1e-6
    assert all(allowed[i,j] for i,j in enumerate(z))
    assert np.max(np.diff(history)) <= 1e-8
    assert risk(A,one_hot(z,3),S) <= history[0]+1e-8


@pytest.mark.parametrize("seed",range(10))
def test_swaps_preserve_quota_and_decrease_risk(seed):
    rng=np.random.default_rng(seed)
    A=rng.normal(size=(4,12)); V=rng.normal(size=(3,3)); S=V@V.T
    labels=np.tile(np.arange(3),4); free=np.arange(3,12)
    allowed=rng.random((12,3))>.2
    allowed[np.arange(12),labels]=True
    z,history=quota_swaps(A,S,labels,free,allowed=allowed)
    assert np.all(allowed[np.arange(12),z])
    assert np.array_equal(z[:3],labels[:3])
    assert np.array_equal(np.bincount(z),np.bincount(labels))
    assert np.max(np.diff(history),initial=-np.inf) < 1e-9
    assert np.isclose(history[-1],risk(A,one_hot(z,3),S))
    # Independently verify no improving legal pair survives.
    for i,j in itertools.combinations(free,2):
        alt=z.copy(); alt[i],alt[j]=alt[j],alt[i]
        if np.all(allowed[np.arange(12),alt]):
            assert risk(A,one_hot(alt,3),S) >= history[-1]-1e-8


def test_quota_relaxation_against_all_feasible_assignments():
    rng=np.random.default_rng(400)
    A=rng.random((2,6)); S=np.eye(3); allowed=np.ones((6,3),bool)
    Q,lower,residual=fractional_optimum(A,S,allowed,[2,2,2])
    values=[risk(A,one_hot(z,3),S) for z in itertools.product(range(3),repeat=6) if np.array_equal(np.bincount(z,minlength=3),[2,2,2])]
    assert lower <= min(values)+1e-7
    assert residual < 1e-7


def test_resolvent_against_iterated_cascade():
    rng=np.random.default_rng(341)
    H=rng.dirichlet(np.ones(4),size=10).T
    for radius in [0,.4,.75,.95]:
        A,B,E=exposure_map(H,np.ones(10)/10,np.ones(4),radius)
        iteration=E.copy()
        for _ in range(1000): iteration=E+B@iteration
        assert np.allclose(iteration,A,rtol=1e-10,atol=1e-10)
        assert np.isclose(max(abs(np.linalg.eigvals(B))),radius)
    with pytest.raises(ValueError): exposure_map(H,np.ones(10),np.ones(4),1.)


def test_identical_error_has_no_diversification_gain():
    rng=np.random.default_rng(71)
    A=rng.normal(size=(4,13)); S=np.ones((3,3))
    target=np.sum(A,axis=1)@np.sum(A,axis=1)
    for _ in range(20):
        Q=rng.dirichlet(np.ones(3),size=13)
        assert np.isclose(risk(A,Q,S),target)
        assert abs(routing_premium(A,Q,S)) < 1e-12


@pytest.mark.parametrize("n,k",[(4,2),(4,4),(20,3),(48,6)])
def test_effective_exposure_granularity(n,k):
    rng=np.random.default_rng(n+k)
    A=rng.lognormal(size=(6,n));Q=np.full((n,k),1/k)
    neff=np.sum(A.sum(axis=1)**2)/np.sum(A**2)
    assert 1-1e-12 <= neff <= n+1e-12
    assert np.isclose(random_routing_risk(A,Q,np.eye(k))/risk(A,Q,np.eye(k)),1+(k-1)/neff)


def test_orthogonal_exposures_show_nonvanishing_integrality_gap():
    A=np.eye(12); k=4; Q=np.full((12,k),1/k)
    rng=np.random.default_rng(7)
    for _ in range(20):
        z=rng.integers(k,size=12)
        assert np.isclose(risk(A,one_hot(z,k),np.eye(k)),12.)
    assert np.isclose(risk(A,Q,np.eye(k)),3.)
    assert np.isclose(random_routing_risk(A,Q,np.eye(k)),12.)


def test_lower_error_model_can_make_diversification_harmful():
    A=np.array([[.2,.3,.5]])
    S=np.array([[1.,1.5],[1.5,4.]])
    for weight in np.linspace(0,1,101):
        Q=np.tile([weight,1-weight],(3,1))
        assert risk(A,Q,S) >= 1-1e-12


def test_robust_spectral_envelope():
    rng=np.random.default_rng(6)
    A=rng.normal(size=(4,8)); Q=rng.dirichlet(np.ones(3),size=8)
    V=rng.normal(size=(3,3)); S=V@V.T; delta=.3
    bound=risk(A,Q,S)+delta*np.sum((A@Q)**2)
    assert np.isclose(bound,risk(A,Q,S+delta*np.eye(3)))
    for _ in range(100):
        D=rng.normal(size=(3,3)); D=D@D.T; D*=delta/np.linalg.norm(D,2)
        assert risk(A,Q,S+D) <= bound+1e-10


def test_ground_truth_satisfies_accounting_equation():
    tasks=generate_tasks()
    assert len({t['id'] for t in tasks})==256
    assert sum(t['split']=='test' for t in tasks)==128
    assert {t['exact_trade'][0]=='-' for t in tasks}=={False,True}
    for t in tasks:
        u=exact_trade(t['nav'],t['risky'],t['target'],t['fee'])
        risky=Decimal(str(t['risky'])); nav=Decimal(str(t['nav']))
        w=Decimal(str(t['target'])); fee=Decimal(str(t['fee']))
        assert abs(risky+u-w*(nav-fee*abs(u))) < Decimal('1e-30')
    for bad in ['', '{"trade_dollars":true}', '{"trade_dollars":"5"}', '{"x":1}', 'NaN']:
        assert parse_trade(bad)==(0.,False)
