"""Exact second-moment calculations; S is uncentered E[e e^T]."""
import numpy as np


def one_hot(labels, k):
    return np.eye(k)[np.asarray(labels, dtype=int)]


def psd_sqrt(S):
    S = np.asarray(S, float)
    values, vectors = np.linalg.eigh((S + S.T) / 2)
    if values.min() < -1e-9 * max(1., abs(values).max()):
        raise ValueError("Second moment is not positive semidefinite")
    return (vectors * np.sqrt(np.maximum(values, 0))) @ vectors.T


def risk(A, Q, S):
    """Expected squared weighted price displacement for deterministic/split Q."""
    M = np.asarray(A) @ np.asarray(Q)
    return float(np.einsum("aj,jk,ak->", M, S, M))


def routing_premium(A, Q, S):
    """Correction for independently selecting one endpoint per institution."""
    q = np.asarray(Q)
    d = q @ np.diag(S) - np.einsum("ij,jk,ik->i", q, S, q)
    return float(np.dot(np.sum(np.asarray(A)**2, axis=0), d))


def random_routing_risk(A, Q, S):
    return risk(A, Q, S) + routing_premium(A, Q, S)


def exposure_map(H, size, impact, feedback_radius=0.4):
    """Local overlapping-portfolio model.

    H has asset-by-institution nonnegative weights, columns sum to one.
    E = diag(impact) H diag(size) maps relative trade errors to price changes.
    B is a normalized nonnegative overlap matrix with declared spectral radius.
    A solves (I-B) A = E; no empirical calibration is implied.
    """
    H = np.asarray(H, float)
    if not 0 <= feedback_radius < 1:
        raise ValueError("feedback radius must lie in [0,1)")
    if np.any(H < 0) or not np.allclose(H.sum(axis=0), 1):
        raise ValueError("portfolio columns must be nonnegative and sum to one")
    if np.any(np.asarray(size) <= 0) or np.any(np.asarray(impact) <= 0):
        raise ValueError("sizes and impact must be positive")
    E = np.asarray(impact)[:, None] * H * np.asarray(size)[None, :]
    overlap = E @ H.T
    radius = float(np.max(np.abs(np.linalg.eigvals(overlap))))
    B = overlap * (feedback_radius / radius) if radius else np.zeros_like(overlap)
    return np.linalg.solve(np.eye(H.shape[0]) - B, E), B, E


def waterfill(base, mass):
    """Minimum squared loads with fixed survivor loads and movable mass."""
    base = np.asarray(base, float)
    if base.ndim != 1 or len(base) == 0 or np.any(base < 0) or mass < 0:
        raise ValueError("nonempty nonnegative loads and mass required")
    lo, hi = float(base.min()), float(base.max() + mass)
    for _ in range(100):
        level = (lo + hi) / 2
        if np.maximum(level - base, 0).sum() < mass:
            lo = level
        else:
            hi = level
    return np.maximum(base, (lo + hi) / 2)
