import numpy as np
import numpy.linalg
import math
import scipy.fftpack
import pylab as p

def cov(x):
    return 1
    cv = x**-1.0
    cv[cv==np.inf]=0
    cv[cv!=cv]=0
    return cv

def filt(x,level=0,maxlevel=0):
    f = np.ones_like(x)

    if level<maxlevel:
        f[len(f)/2:]=0
    if level>0:
        f[:len(f)/4] = 0

    return f

class MultiscaleGaussian(object):
    def __init__(self, cov_fn=cov, n_refine=0, size=256):
        self.cov_fn = cov
        self.n_refine = n_refine
        self.size = size


    def realization(self, level=0, means=None):
        delta = 0.5**(level)/self.size
        r = np.random.normal(0.0,1.0,size=self.size)
        r*=np.sqrt(cov(scipy.fftpack.rfftfreq(self.size,d=delta)) * self.size)
        r*=np.exp(np.random.uniform(0.0,2*math.pi,size=self.size)*1.j)
        r*=filt(r,level,self.n_refine)


        r = scipy.fftpack.irfft(r)

        if means is not None:
            #means/=np.sqrt(2)

            means_c = np.concatenate([[means[-1]],means[:self.size/2+1]])
            means_c = means[:self.size/2+2]

            means_expanded = np.zeros(self.size)
            means_expanded[::2] = 2*means_c[1:-1]/3+means_c[:-2]/3
            means_expanded[1::2] = 2*means_c[1:-1]/3+means_c[2:]/3

            #means_expanded = scipy.fftpack.rfft(means_expanded)
            #means_expanded*=(1.-filt(r,level,self.n_refine))
            #means_expanded = scipy.fftpack.irfft(means_expanded)

            r+=means_expanded


        if level==self.n_refine:
            return [r]
        else:
            return [r]+self.realization(level+1,r)

    def xs(self):
        xs = []
        for i in range(self.n_refine+1):
            xs.append(np.arange(self.size,dtype=float)/2**i)
        return xs

    def estimate_cov(self, level, Ntrials=4000):
        cov = np.zeros((self.size,self.size))
        for i in xrange(Ntrials):
            r = self.realization()[level]
            cov+=np.outer(r,r)
        return cov

    def estimate_covs(self, Ntrials=4000):
        cov = np.zeros(((self.size*(self.n_refine+1),(self.size*(self.n_refine+10)))))

        for i in xrange(Ntrials):
            r = self.realization()
            for l1 in range(self.n_refine+1):
                for l2 in range(self.n_refine+1):
                    cov[l1*self.size:(l1+1)*self.size,l2*self.size:(l2+1)*self.size]+=np.outer(r[l1],r[l2])

        return cov


def demo():
    np.random.seed(1)
    G = MultiscaleGaussian(cov, 1)

    G2 = MultiscaleGaussian(cov, 0,512)

    x0, x1 = G.xs()
    r0,r1 = G.realization()
    p.plot(x0,r0)
    p.plot(x1,r1)

    x0 = G2.xs()[0]/2
    r0, = G2.realization()
    p.plot(x0,r0)

def display_multicov(covs, base_size=256, vmin=None, vmax=None, base_extent=None):
    if not vmin:
        vmin = covs.min()
        vmax = covs.max()

    nrefine = len(covs)/base_size
    assert nrefine*base_size==len(covs)

    if not base_extent:
        base_extent = base_size*2**nrefine


    # the base layer
    print "display",base_extent
    p.imshow(covs[:base_size,:base_size],extent=[0,base_extent,base_extent,0],vmin=vmin,vmax=vmax)
    p.plot([0,base_extent,base_extent,0,0],[0,0,base_extent,base_extent,0],'w-')

    if nrefine>1:
        # diagonals between the refined regions and the current region
        p.imshow(covs[base_size/2:base_size,base_size:2*base_size],
                 extent=[0,base_extent/2,base_extent,base_extent/2],vmin=vmin,vmax=vmax)
        p.imshow(covs[base_size:2*base_size,base_size/2:base_size],
                 extent=[base_extent/2,base_extent,base_extent/2,0],vmin=vmin,vmax=vmax)



        # the refined region
        display_multicov(covs[base_size:,base_size:],base_size,vmin=vmin,vmax=vmax,base_extent=base_extent/2)

        p.plot([base_extent/2,base_extent],[base_extent/2,base_extent/2],"w:")
        p.plot([base_extent/2,base_extent/2],[base_extent/2,base_extent],'w:')

        p.xlim(0,base_extent)
        p.ylim(base_extent,0)

def demo_cov(base_size=128,nrefine=3):
    G = MultiscaleGaussian(cov, nrefine, size=base_size)
    cv1 = G.estimate_cov(nrefine)
    p.clf()
    p.subplot(131)
    vmin = cv1.min()
    vmax = cv1.max()
    p.imshow(cv1,vmin=vmin,vmax=vmax)

    G = MultiscaleGaussian(cov,0, base_size*2**nrefine)
    cv2 = G.estimate_cov(0)[:base_size,:base_size]

    p.subplot(132)
    p.imshow(cv2,vmin=vmin,vmax=vmax)

    p.subplot(133)
    p.imshow(cv1-cv2[:256,:256],vmin=-vmax,vmax=vmax)

def demo_multicov(base_size=128,nrefine=3):
    covs = MultiscaleGaussian(cov, nrefine, size=base_size).estimate_covs()
    p.subplot(121)
    vmin = covs.min()
    vmax = covs.max()
    display_multicov(covs,base_size)
    p.subplot(122)
    p.imshow(covs[:base_size,:base_size],vmin=vmin,vmax=vmax)