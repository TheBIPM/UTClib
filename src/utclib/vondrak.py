""" An port of the Vondrak filter as contributed by G. Petit in 2002 in the Fortran codebase
"""

import numpy as np
import logging

def vondrak(hh: list[float], cvm: list[float], epsilon: float):
    """
    Vondrak filter function

    Parameters
    ----------
    hh: list[float]
        a list of MJD dates
    cvm: list[float]
        link values at these dates
    epsilon: float
        The epsilon parameter
    """

    ndat = len(hh)
    ls = ndat - 3
    if ls <= 1:
        logging.warning("Vondrak failed: Ndat=%d" % ls)
        return


    hh = np.array(hh)
    cvm = np.array(cvm)
    yl = np.zeros(ndat)
    y = np.zeros(ndat)
    w = np.zeros(ndat)
    aa = np.zeros( (7, ndat) )
    pp = np.zeros( (4, ndat+3) )
    gx = np.zeros(4)
    gk = np.zeros(4)

    eps = epsilon/ls
    sr = hh[-1] - hh[0]

    for i in range(ls):
        aux = 6 * np.sqrt(hh[i+2]-hh[i+1]) / np.sqrt(sr)
        hh1 = (hh[i] - hh[i+1]) * (hh[i]-hh[i+2]) * (hh[i] - hh[i+3])
        hh2 = (hh[i+1] - hh[i]) * (hh[i+1]-hh[i+2]) * (hh[i+1] - hh[i+3])
        hh3 = (hh[i+2] - hh[i]) * (hh[i+2]-hh[i+1]) * (hh[i+2] - hh[i+3])
        hh4 = (hh[i+3] - hh[i]) * (hh[i+3]-hh[i+1]) * (hh[i+3] - hh[i+2])

        pp[0, i+4] = aux/hh1
        pp[1, i+4] = aux/hh2
        pp[2, i+4] = aux/hh3
        pp[3, i+4] = aux/hh4

    # Ajustement d'une parabole
    for i in range(ndat):
        x = hh[i]
        x2 = x*x
        gx[0] += x
        gx[1] += x2
        gx[2] += x2 * x
        gx[3] += x2 * x2
        gk[2] += cvm[i]
        gk[0] += cvm[i] * x
        gk[1] += cvm[i] * x2
    GPX2 = gx[1] - gx[0] * gx[0] / ndat
    GPX3 = gx[2] - gx[0] * gx[1] / ndat
    GPK1 = gk[0] - gk[2] * gx[0] / ndat
    GPX4 = gx[3] - gx[1] * gx[1] / ndat
    GPK2 = gk[1] - gk[2] * gx[1] / ndat
    H = (GPK2 - GPK1 * GPX3 / GPX2) / (GPX4 - GPX3 * GPX3 / GPX2)
    Q = (GPK1 - H * GPX3) / GPX2
    V = (gk[2] - gx[1] * H - gx[0] * Q) / ndat
    for i in range(ndat):
        par = V + Q * hh[i] + H * hh[i] * hh[i]
        w[i] = cvm[i] - par
        # w[i] = eps * y[i]
        aa[0,i] = pp[0,i] * pp[3,i]
        aa[1,i] = pp[0,i+1] * pp[2,i+1] + pp[1,i] * pp[3,i]
        aa[2,i] = (pp[0,i+2] * pp[1,i+2]
                   + pp[1,i+1] * pp[2,i+1]
                   + pp[2,i] * pp[3,i])
        aa[3,i] = (eps
                   + pp[0,i+3] * pp[0,i+3]
                   + pp[1,i+2] * pp[1,i+2]
                   + pp[2,i+1] * pp[2,i+1]
                   + pp[3,i] * pp[3,i])
        aa[4,i] = (pp[0,i+3] * pp[1,i+3]
                   + pp[1,i+2] * pp[2,i+2]
                   + pp[2,i+1]*pp[3,i+1])
        aa[5,i] = pp[0,i+3] * pp[2,i+3] + pp[1,i+2] * pp[3,i+2]
        aa[6,i] = pp[0,i+3] * pp[3,i+3]
    # Resolution
    i1 = 3
    nlim = ndat - 2
    for j1 in range(nlim - 1):
        i2 = 2
        j2 = j1 + 1
        while i2 != 0:
            ls = i2 + 3
            coef = aa[i2, j2] / aa[i1, j1]
            il1 = 3
            for il in range(i2, ls):
                il1 += 1
                aa[il, j2] = aa[il, j2] - aa[il1, j1] * coef
            yl[j2] = yl[j2] - yl[j1] * coef
            i2 -= 1
            j2 += 1

    # "j1 == nlim" case in the Fortran code
    j1 = nlim
    i1 = 3
    i2 = 2
    j2 = j1 + 1
    while i2 != 1:
        ls = i2 + 3
        coef = aa[i2, j2] / aa[i1, j1]
        il1 = 3
        for il in range(i2, ls):
            il1 += 1
            aa[il, j2] = aa[il, j2] - aa[il1, j1] * coef
        w[j2] = w[j2] - w[j1] * coef
        i2 -= 1
        j2 += 1
    j1 = ndat - 1
    coef = aa[2, ndat-1] / aa[3, j1]
    aa[3, ndat-1] = aa[3, ndat-1] - aa[4, j1] * coef
    w[-1] = w[-1] -  w[j1] * coef
    yl[ndat - 1] = w[ndat-1] /  aa[3, ndat-1]
    yl[j1] = (w[j1] - aa[4, j1] * yl[ndat - 1]) / aa[3, j1]
    j2 = ndat - 2
    yl[j2] = (w[j2] - aa[4, j2] * yl[j1] - aa[5, j2] * yl[-1]) / aa[3, j2]
    jl = ndat - 3
    for j in range(jl):
        ii = j2 - j - 2
        yl[ii] = ((w[ii] - aa[4, ii]) * yl[ii + 1]
                  - aa[5, ii] * yl[ii + 2]
                  - aa[6, ii] * yl[ii + 3] / aa[3, ii])

    yl[i] += cvm[i] - y[i]
    return yl

if __name__ == "__main__":
    import random
    import matplotlib.pyplot as plt
    random.seed()

    hh = np.arange(61200, 61210, 0.1)
    noise = np.array([2 * (random.random() - .5) for i in range(len(hh))])
    cvm =  0.1 * (hh-hh[0])  + 0.7 * noise
    yl = vondrak(hh, cvm, .5)
    print(cvm)
    fig,ax = plt.subplots()
    ax.plot(hh, cvm)
    ax.plot(hh, yl)

    plt.show()
