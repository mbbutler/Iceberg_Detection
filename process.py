import sqlite3 as lite
import matplotlib.pyplot as plt
import sys
from osgeo import gdal, gdalnumeric
from osgeo import *
from gdalconst import *
import numpy as np
import ogr
import os
import fnmatch
from scipy import ndimage
from scipy.optimize import curve_fit



def exp_func(x, *p):
    A, tau = p
    return A*numpy.exp(-(x)/(tau))



############ MAIN ###########

if len(sys.argv) != 3:
    print "Usage is:   python process.py [full path of directory to be processed] [min size]"
    exit()
    
path = sys.argv[1]
min_size = int(sys.argv[2])

if path[-1] != '/':
    path += '/'
    
##con = lite.connect('test.db')
##print 'connected okay'
##db = con.cursor()
##db.execute('''DROP TABLE Icebergs''')
##con.commit()
##db.execute('''CREATE TABLE Icebergs(Day INT, X REAL, Y REAL, Size INT)''')
##con.commit()

files = [f for f in os.listdir(path) if os.path.isfile(path + f)]

for f in files:
    if fnmatch.fnmatch(f, '*.TIF'):
        # Create and open text output file (use a for append, w for write)
        output = open(path + f[:-4] + '_clusters.txt', 'w',)

        print 'Processing file ', f
        ds = gdal.Open(path + f)
        geo = ds.GetGeoTransform()
        x_start = geo[0]
        y_start = geo[3]
        band = ds.GetRasterBand(1).ReadAsArray()
        
        # Use numpy's label function to cluster pixels
        label_im, nb_labels = ndimage.label(band)
        print "# clusters = ", nb_labels

        # find_objects returns slices of array that contain each cluster
        iceberg_list = ndimage.find_objects(label_im)

        temp = np.empty(nb_labels)
        count = 0

        day = f[:-8]
        icebergs = []
        for slic in iceberg_list:
            y_off = y_start + slic[0].start * geo[5]
            x_off = x_start + slic[1].start * geo[1]
            array = label_im[slic]
            size = np.count_nonzero(array)
            if size >= min_size:
                y,x = np.nonzero(array)
                y_avg = np.sum(y)/float(size)
                x_avg = np.sum(x)/float(size)
                y_cent = y_off + geo[5]*y_avg
                x_cent = x_off + geo[1]*x_avg
                new_iceberg = (day, x_cent, y_cent, size)
                line = str(day) + ',' + str(x_cent) + ',' + str(y_cent) + ',' + str(size) + '\n'
                output.write(line)
                icebergs.append(new_iceberg)
                temp[count] = size
                count += 1
             
        hist_temp = np.empty(count)   
        for i in range(count):
            hist_temp[i] = temp[i]
            
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


##    db.executemany('INSERT INTO Icebergs VALUES (?,?,?,?)', icebergs)
##    con.commit()
    ds = None
##
##con.close()
output.close()
            
