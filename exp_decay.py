import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np
import sys

def exp_func(x, *p):
    A, tau = p
    return A*np.exp(-(x)/(tau))


if len(sys.argv) != 2:
    print "Usage is: python process.py [file to be processed]"
    exit()
    
fname = sys.argv[1]

hist_temp= np.loadtxt(fname, dtype='uint8', usecols=[3], delimiter=',')

a_max = np.amax(hist_temp)
hist, bin_edges = np.histogram( hist_temp, bins=np.arange(1,a_max+2) )

bin_centers = (bin_edges[:-1] + bin_edges[1:])/2

p0 = [100., 1.]
coeff, var_matrix = curve_fit(exp_func, bin_centers, hist, p0=p0)

print 'Fitted Amplitude = ', coeff[0]
print 'Fitted decay constant = ', coeff[1]

hist_fit = exp_func(bin_centers, *coeff)

plt.plot(bin_centers, hist, label='Test data')
plt.plot(bin_centers, hist_fit, label='Fitted data')
plt.show()
