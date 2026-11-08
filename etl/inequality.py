import numpy as np


def gini(x, w):
    o = np.argsort(x); x, w = x[o], w[o]
    cw = np.cumsum(w) / w.sum(); cx = np.cumsum(x * w) / (x * w).sum()
    return 1 - np.sum((cw - np.r_[0, cw[:-1]]) * (cx + np.r_[0, cx[:-1]]))


def palma(x, w):
    x, w = np.asarray(x, dtype=float), np.asarray(w, dtype=float)
    if x.shape != w.shape or x.ndim != 1:
        raise ValueError("values and weights must be matching one-dimensional arrays")
    if np.any(w[np.isfinite(w)] < 0) or np.any(x[np.isfinite(x)] < 0):
        raise ValueError("values and weights must be nonnegative")
    valid = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[valid], w[valid]
    if not len(x):
        return np.nan
    order = np.argsort(x, kind="stable")
    x, w = x[order], w[order]
    end = np.cumsum(w / w.sum())
    start = np.r_[0., end[:-1]]
    bottom = np.sum(x * np.maximum(0., np.minimum(end, 0.4) - start))
    top = np.sum(x * np.maximum(0., end - np.maximum(start, 0.9)))
    if bottom == 0:
        return np.inf if top > 0 else np.nan
    return top / bottom


def theil(x, w):
    m = np.average(x, weights=w)
    r = np.where(x > 0, x / m, 1)
    return np.average(np.where(x > 0, r * np.log(r), 0), weights=w)


