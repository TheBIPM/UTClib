""" An port of the Vondrak filter as contributed by G. Petit in 2002 in the Fortran codebase
"""

import numpy as np
import logging

def vondrak(x: list[float], y: list[float], epsilon: float):
    """
    Vondrak filter function

    Parameters
    ----------
    x: list[float]
        a list of MJD dates
    y: list[float]
        link values at these dates
    epsilon: float
        The epsilon parameter
    """

    ndat = len(x)
    ls = ndat - 3
    if ls <= 1:
        logging.warning("Vondrak failed: Ndat=%d" % ls)
        return

    # Fortran convention used for numbering, row 0 not used, one additional
    # element added on all dimensions
    hh = np.zeros(ndat + 1)
    hh[1:] = x
    cvm = np.zeros(ndat + 1)
    cvm[1:] = y

    yl = np.zeros(ndat + 1)
    y = np.zeros(ndat + 1)
    w = np.zeros(ndat + 1)
    aa = np.zeros( (8, ndat + 1) )
    pp = np.zeros( (5, ndat + 4) )
    gx = np.zeros(5)
    gk = np.zeros(5)

    eps = epsilon/ls
    j = 3
    sr = hh[-1] - hh[1]
    for i in range(1, ls + 1):
        aux = 6 * np.sqrt(hh[i+2]-hh[i+1]) / np.sqrt(sr)
        j += 1

        hh1 = (hh[i] - hh[i+1]) * (hh[i]-hh[i+2]) * (hh[i] - hh[i+3])
        hh2 = (hh[i+1] - hh[i]) * (hh[i+1]-hh[i+2]) * (hh[i+1] - hh[i+3])
        hh3 = (hh[i+2] - hh[i]) * (hh[i+2]-hh[i+1]) * (hh[i+2] - hh[i+3])
        hh4 = (hh[i+3] - hh[i]) * (hh[i+3]-hh[i+1]) * (hh[i+3] - hh[i+2])

        pp[1, j] = aux/hh1
        pp[2, j] = aux/hh2
        pp[3, j] = aux/hh3
        pp[4, j] = aux/hh4

    # Ajustement d'une parabole
    for i in range(1, ndat + 1):
        x = hh[i]
        x2 = x*x
        gx[1] += x
        gx[2] += x2
        gx[3] += x2 * x
        gx[4] += x2 * x2
        gk[3] += cvm[i]
        gk[1] += cvm[i] * x
        gk[2] += cvm[i] * x2
    GPX2 = gx[2] - gx[1] * gx[1] / ndat
    GPX3 = gx[3] - gx[1] * gx[2] / ndat
    GPK1 = gk[1] - gk[3] * gx[1] / ndat
    GPX4 = gx[4] - gx[2] * gx[2] / ndat
    GPK2 = gk[2] - gk[3] * gx[2] / ndat
    H = (GPK2 - GPK1 * GPX3 / GPX2) / (GPX4 - GPX3 * GPX3 / GPX2)
    Q = (GPK1 - H * GPX3) / GPX2
    V = (gk[3] - gx[2] * H - gx[1] * Q) / ndat
    for i in range(1, ndat+1):
        par = V + Q * hh[i] + H * hh[i] * hh[i]
        y[i] = cvm[i] - par
        w[i] = eps * y[i]
        aa[1,i] = pp[1,i] * pp[4,i]
        aa[2,i] = pp[1,i+1] * pp[3,i+1] + pp[2,i] * pp[4,i]
        aa[3,i] = (pp[1,i+2] * pp[2,i+2]
                   + pp[2,i+1] * pp[3,i+1]
                   + pp[3,i] * pp[4,i])
        aa[4,i] = (eps
                   + pp[1,i+3] * pp[1,i+3]
                   + pp[2,i+2] * pp[2,i+2]
                   + pp[3,i+1] * pp[3,i+1]
                   + pp[4,i] * pp[4,i])
        aa[5,i] = (pp[1,i+3] * pp[2,i+3]
                   + pp[2,i+2] * pp[3,i+2]
                   + pp[3,i+1]*pp[4,i+1])
        aa[6,i] = pp[1,i+3] * pp[3,i+3] + pp[2,i+2] * pp[4,i+2]
        aa[7,i] = pp[1,i+3] * pp[4,i+3]
    # Resolution (following the  F314.for code, as modernized)
    # This follows quite closely the instructions from Vondrak1969
    j1 = 0
    nlim = ndat - 2
    while (j1 != nlim - 1):
        i1 = 4
        j1 += 1
        i2 = 3
        j2 = j1 + 1
        while (i2 != 0):
            coef = aa[i2, j2] / aa[i1, j1]
            ls = i2 + 3
            il1 = 3
            for il in range(i2, ls+1):
                il1 += 1
                aa[il, j2] = aa[il, j2] - aa[il1, j1] * coef
            w[j2] = w[j2] - w[j1] * coef
            i2 -= 1
            j2 += 1
    i1 = 4
    j1 = ndat - 2
    i2 = 3
    j2 = ndat - 1
    while (i2 != 1):
        ls = i2 + 2
        coef = aa[i2, j2] / aa[i1, j1]
        il1 = 3
        for il in range(i2, ls + 1):
            il1 += 1
            aa[il, j2] = aa[il, j2] - aa[il1, j1] * coef
        w[j2] = w[j2] - w[j1] * coef
        i2 -= 1
        j2 += 1
    j1 = ndat - 1
    coef = aa[3, ndat - 1] / aa[4, j1]
    aa[4, ndat] = aa[4, ndat] - aa[5, j1] * coef
    w[ndat] = w[ndat] - w[j1]*coef
    yl[ndat] = w[ndat] / aa[4, ndat]
    yl[j1] = (w[j1] - aa[5, j1] * yl[ndat]) / aa[4, j1]
    j2 = ndat - 2
    yl[j2] = (w[j2] - aa[5, j2] * yl[j1] - aa[6, j2] * yl[ndat]) / aa[4, j2]
    jl = ndat - 3
    for j in range(1, jl + 1):
        ii = j2 - j
        yl[ii] =(w[ii] - aa[5, ii] * yl[ii+1]
                 - aa[6, ii] * yl[ii+2]
                 - aa[7, ii] * yl[ii+3]) / aa[4, ii]
    for i in range(1, ndat +1):
        yl[i] = yl[i] + cvm[i] - y[i]
    return yl[1:]



def vondrak2(x: list[float], y: list[float], eps: float):
    """ Rewrite using the original article's notations
    """

    x = np.array(x)
    y = np.array(y)
    n = len(x)
    # a[i] (and b,c,d) = 0 outside of [1, n-3]
    a = np.zeros(n)
    b = np.zeros(n)
    c = np.zeros(n)
    d = np.zeros(n)

    for i in range(1, n-3):
        aux = 6 * np.sqrt(x[i+2] - x[i+1])
        a[i] = aux / ((x[i] - x[i+1]) * (x[i] - x[i+2]) * (x[i] - x[i+3]))
        b[i] = aux / ((x[i+1] - x[i]) * (x[i+1] - x[i+2]) * (x[i+1] - x[i+3]))
        c[i] = aux / ((x[i+2] - x[i]) * (x[i+2] - x[i+1]) * (x[i+2] - x[i+3]))
        d[i] = aux / ((x[i+3] - x[i]) * (x[i+3] - x[i+1]) * (x[i+3] - x[i+2]))

    A = np.zeros( (7, n) )
    A[0, 3:] = a[:-3] * d[:-3]
    A[1, 3:] = a[1:-2] * c[1:-2] + b[:-3] * d[:-3]
    A[2, 3:] = a[2:-1] * b[2:-1] + b[1:-2] * d[:-3]
    A[3, 3:] = a[3:]**2 + b[2:-1]**2 + c[1:-2]**2 + d[:-3]**2
    A[4, 3:] = a[3:] * b[3:] + b[2:-1] * c[2:-1]  + c[1:-2] * d[1:-2]
    A[5, 3:] = a[3:] * c[3:] + b[2:-1] * d[2:-1]
    A[6, 3:] = a[3:] * d[3:]

    import ipdb;ipdb.set_trace()  # noqa


if __name__ == "__main__":

    import matplotlib.pyplot as plt
    data = np.loadtxt("input_data.txt")
    hh = data[:, 0].tolist()
    cvm = data[:, 1].tolist()
    yl = vondrak(hh, cvm, .5)

    fig,ax = plt.subplots()
    ax.plot(hh, cvm)
    ax.plot(hh, yl)
    with open('output_python.txt', 'w') as fp:
        for i in range(len(hh)):
            fp.write('{:13.6f} {:10.3f} {:10.3f}\n'.format(hh[i], cvm[i], yl[i]))
