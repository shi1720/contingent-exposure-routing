"""Convex lower bounds and implementable endpoint assignments.

Quota-preserving swaps are a local-search heuristic, not a global optimizer.
The conditional-expectation guarantee applies without coupled quota constraints.
"""
import numpy as np
import cvxpy as cp
from .risk import risk, random_routing_risk, one_hot, psd_sqrt


def eligibility(primary, survivors):
    n, k = len(primary), max(max(primary) + 1, max(survivors) + 1)
    allowed = np.zeros((n, k), bool)
    for i, j in enumerate(primary):
        allowed[i, j if j in survivors else survivors] = True
    return allowed


def count_balanced(primary, survivors, rng):
    z = np.asarray(primary).copy()
    free = np.flatnonzero(~np.isin(z, survivors))
    free = rng.permutation(free)
    counts = np.bincount(z[np.isin(z, survivors)], minlength=max(primary)+1)
    for i in free:
        j = min(survivors, key=lambda j: (counts[j], j))
        z[i] = j
        counts[j] += 1
    return z, free


def fractional_optimum(A, S, allowed, quotas=None):
    n, k = allowed.shape
    Q = cp.Variable((n, k))
    constraints = [Q >= 0, cp.sum(Q, axis=1) == 1, Q[~allowed] == 0]
    if quotas is not None:
        constraints += [cp.sum(Q, axis=0) == quotas]
    # Rescale objective for solver stability without altering its minimizer.
    scale = max(risk(A, allowed / allowed.sum(axis=1, keepdims=True), S), 1e-15)
    problem = cp.Problem(cp.Minimize(cp.sum_squares(A @ Q @ psd_sqrt(S)) / scale), constraints)
    problem.solve(solver="CLARABEL", tol_gap_abs=1e-9, tol_feas=1e-9, tol_gap_rel=1e-9, max_iter=300)
    if problem.status not in {"optimal", "optimal_inaccurate"}:
        raise RuntimeError(f"Convex solver failed: {problem.status}")
    value = np.asarray(Q.value)
    residual = max(float(np.max(np.abs(value.sum(axis=1)-1))),
                   float(np.max(np.abs(value[~allowed]), initial=0.)), max(0., float(-value.min())))
    if quotas is not None:
        residual = max(residual, float(np.max(np.abs(value.sum(axis=0)-quotas))))
    # Supporting-hyperplane bound with explicitly feasible transportation dual.
    # A feasible primal objective alone is NOT a lower bound for minimization.
    gradient = 2*A.T @ (A @ value) @ S
    v = -np.asarray(constraints[-1].dual_value)*scale if quotas is not None else np.zeros(k)
    u = np.min(np.where(allowed, gradient-v[None,:], np.inf), axis=1)
    linear_lower = u.sum() + (np.dot(quotas,v) if quotas is not None else 0.)
    lower = risk(A,value,S) - np.sum(gradient*value) + linear_lower
    return value, float(lower), residual


def conditional_round(A, Q, S, allowed=None):
    """Derandomize exact independent-routing objective one row at a time."""
    Q = np.maximum(np.asarray(Q, float), 0).copy()
    if allowed is None:
        allowed = Q > 1e-12
    Q[~allowed] = 0
    Q /= Q.sum(axis=1, keepdims=True)
    history = [random_routing_risk(A, Q, S)]
    for i in np.argsort(-np.linalg.norm(A, axis=0), kind="stable"):
        trials = []
        for j in np.flatnonzero(allowed[i]):
            test = Q.copy()
            test[i] = np.eye(Q.shape[1])[j]
            trials.append((random_routing_risk(A, test, S), j))
        _, j = min(trials)
        Q[i] = np.eye(Q.shape[1])[j]
        history.append(random_routing_risk(A, Q, S))
    return np.argmax(Q, axis=1), np.asarray(history)


def quota_swaps(A, S, labels, free, max_swaps=2000, allowed=None):
    """Best-improvement swaps, preserving all endpoint counts and fixed rows."""
    z = np.asarray(labels).copy()
    k = S.shape[0]
    if allowed is not None and not np.all(allowed[np.arange(len(z)),z]):
        raise ValueError("Initial assignment violates eligibility")
    M = A @ one_hot(z, k)
    current = risk(A, one_hot(z, k), S)
    history = [current]
    ii, jj = np.triu_indices(len(free), 1)
    left, right = np.asarray(free)[ii], np.asarray(free)[jj]
    if len(left) == 0:
        return z, np.asarray(history)
    D = A[:, left] - A[:, right]
    d2 = (D**2).sum(axis=0)
    for _ in range(max_swaps):
        p, q = z[left], z[right]
        MS = M @ S
        delta = 2*np.sum(D*(MS[:, q]-MS[:, p]), axis=0)
        delta += d2*(S[p,p]+S[q,q]-2*S[p,q])
        delta[p == q] = np.inf
        if allowed is not None:
            delta[~(allowed[left,q] & allowed[right,p])] = np.inf
        at = int(np.argmin(delta))
        if delta[at] >= -1e-12 * max(1., current):
            break
        i, j = int(left[at]), int(right[at])
        p, q = z[i], z[j]
        d = A[:, i]-A[:, j]
        M[:, p] -= d
        M[:, q] += d
        z[i], z[j] = q, p
        current = float(np.einsum("aj,jk,ak->", M, S, M))
        history.append(current)
    return z, np.asarray(history)
