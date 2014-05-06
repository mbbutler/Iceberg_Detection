from osgeo import gdal, gdalnumeric
from osgeo import *
import sys
from gdalconst import *
import numpy as np
import ogr
import os
import fnmatch
from scipy import ndimage

gdal.UseExceptions()

####### Functions #######

# thresholds the image at a given value
def Threshold(array, thresh_val):
    array[array<thresh_val] = 0
    return array

def Get_Cloud_Mask(band_4, band_5):
    is_zero = (band_5==0)
    band_5[is_zero] = 1
    ratio = np.true_divide(band_4, band_5)
    ratio[is_zero] = 0
    #band_min = np.amin(ratio)
    #band_mean = np.mean(ratio)
    #band_max = 2*band_mean
    #is_over = (ratio > band_max)
    #ratio = 255*(ratio-band_min)/(band_max-band_min)
    #ratio[is_over] = 255
    #ratio = ratio.astype('B')
    ratio = ndimage.zoom(ratio, 2, order=0)
    ratio = np.delete(ratio, 0, 0)
    ratio = np.delete(ratio, 0, 1)
    print 'band_min = ', np.amin(ratio)
    print 'band_max = ', np.amax(ratio)
    print 'band_mean = ', np.mean(ratio)
    return ratio < 1.0
    
    
# Creates raster mask from vector_fn of ds.
# The rasterized mask is named raster_fn
def GetMask(ds, raster_fn, vector_fn):

    # Open vector file and get Layer
    vec_ds = ogr.Open(vector_fn)
    vec_layer = vec_ds.GetLayer()

    # Get GeoTransform of Geotiff to be masked
    geo = ds.GetGeoTransform()

    # Create the mask geotiff
    mask_ds = gdal.GetDriverByName('GTiff').Create(raster_fn, ds.RasterXSize, ds.RasterYSize, gdal.GDT_Byte)
    mask_ds.SetGeoTransform((geo[0], geo[1], geo[2], geo[3], geo[4], geo[5]))
    band = mask_ds.GetRasterBand(1)
    band.SetNoDataValue(0)

    # Rasterize
    gdal.RasterizeLayer(mask_ds, [1], vec_layer, burn_values=[1])

    vec_ds = None
    return mask_ds

# Trim an image according to upperleft x and y coords
# and lowerright x and y coords
def TrimImage(cloud_name, ulx, uly, lrx, lry):
    cut_name = cloud_name[:-4] + "_cut.TIF"
    fullCmd = "gdal_translate -of GTiff -srcwin " + str(ulx) + " " + str(uly) + " " + str(lrx) + " " + str(lry) + " " + cloud_name + " " + cut_name
    os.system(fullCmd)
    return cut_name



def MergeImages(img1, img2, new_name):
    cmd = "gdal_merge.py -o " + new_name + " -ot Byte " + img1 + " " + img2
    os.system(cmd)


def StitchImages(path):

    if path[-1] != '/':
        path += '/'

    save_path = path + 'Combined_Images/'

    cmd = 'mkdir ' + save_path
    os.system(cmd)

    orig_pro_path = path + 'Original_Processed_Images/'
    cmd = 'mkdir ' + orig_pro_path
    os.system(cmd)

    files = [f for f in os.listdir(path) if os.path.isfile(path + '/' + f)]
   
    while files:
        fn = files[0]
        if len(files) == 1:
            cmd = 'mv ' + path + fn + ' ' + save_path + fn[9:16] + '.TIF'
            os.system(cmd)
        else:
            isStitched = False
            for ofn in files[1:]:
                if fn[9:16] in ofn:
                    MergeImages(path + fn, path + ofn, save_path + fn[9:16] + '.TIF')
                    cmd = 'mv ' + path + fn + ' ' + orig_pro_path + fn
                    os.system(cmd)
                    cmd = 'mv ' + path + ofn + ' ' + orig_pro_path + ofn
                    os.system(cmd)
                    isSitched = True
            if not isStitched:
                cmd = 'mv ' + path + fn + ' ' + save_path + fn[9:16] + '.TIF'
                os.system(cmd)

        files = [f for f in os.listdir(path) if os.path.isfile(path + '/' + f)]

def ProcessFolder(path, threshold, save_path):
    
    files = [f for f in os.listdir(path) if os.path.isfile(path + '/' + f)]
    folders = [f for f in os.listdir(path) if os.path.isdir(path + '/' + f)]

    for folder in folders:
        print "Processing Folder: " + folder
        if folder[-1] == '/':
            folder = folder[:-1]
        ProcessFolder(path + '/' + folder, threshold, save_path)

    for f in files:
        if fnmatch.fnmatch(f, '*8.TIF'):
            print "Processing File: " + f
            ProcessFile(path, f, threshold, save_path)


def ProcessFile(path, filename, thresh_value, save_path):

    # Open Geotif that is to be analyzed

    input_file = path + '/' + filename

    print "Opening Band 8..."
    ds = gdal.Open(input_file)

    print "Opening Band 4..."
    ds_4 = gdal.Open(input_file[:-6] + 'B4.TIF')

    print "Opening Band 5..."
    ds_5 = gdal.Open(input_file[:-6] + 'B5.TIF')

    band_4 = ds_4.GetRasterBand(1).ReadAsArray()
    band_5 = ds_5.GetRasterBand(1).ReadAsArray()

    print "Creating Cloud Mask Array..."
    cloud_ind = Get_Cloud_Mask(band_4, band_5)

    ds_4 = None
    ds_5 = None

    print "Apply cloud mask and create new GeoTiff..."
    ds_array = ds.GetRasterBand(1).ReadAsArray()
    print np.amax(ds_array)
    print np.mean(ds_array)
    ds_array[cloud_ind] = 0
    print np.amax(ds_array)
    print np.mean(ds_array)
    geo = ds.GetGeoTransform()
    cloud_name = ds.GetDescription()[:-4] +"_cloud.TIF"
    cmask_ds = gdal.GetDriverByName('GTiff').Create(cloud_name, ds_array.shape[1], ds_array.shape[0], gdal.GDT_Byte)
    cmask_ds.SetGeoTransform((geo[0], geo[1], geo[2], geo[3], geo[4], geo[5]))
    cmask_ds.SetProjection(ds.GetProjection())
    cmask_ds.GetRasterBand(1).WriteArray(ds_array)
    new_array = cmask_ds.GetRasterBand(1).ReadAsArray()
    print np.amax(new_array)
    print np.mean(new_array)
    ds = None
    print "Done."

    # Resize geotif to get rid of extra landmass
    print "Resizing GeoTif..."
    lrx = cmask_ds.RasterXSize
    lry = cmask_ds.RasterYSize
    cmask_ds = None
    ipath = int(filename[3:6])
    irow = int(filename[6:9])
    cut_name = ""
    if ipath == 10:
        if irow == 11:
            cut_name = TrimImage(cloud_name, 0, 0, lrx - (7700), lry)
        elif irow == 12:
            cut_name = TrimImage(cloud_name, 2760, 0, lrx - (2760 + 2500), lry - 8940)
        else:
            print "Wrong row: ", irow

    elif ipath == 11:
        if irow == 11:
            cut_name = TrimImage(cloud_name, 1980, 0, lrx - (1980 + 3510), lry)
        elif irow == 12:
            cut_name = TrimImage(cloud_name, 6880, 0, lrx - (6880), lry - 8910)
        else:
            print "Wrong row: ", irow
            print "Exiting"
            exit()

    else:
        print "Wrong path: ", ipath
        print "Exiting"
        exit()
    
    print "Geotif resized."

    # Close original file and open the resized file
    ds = gdal.Open(cut_name)

    # Create rasterized mask from vector file
    print "Rasterizing vector mask..."
    mask_ds = GetMask(ds, cut_name[:-4] + "_mask.tif", 'AOI_nofjords.shp')
    print "Vector mask has been rasterized."

    # Get Mask 2D raster and apply mask
    mask_array = mask_ds.GetRasterBand(1).ReadAsArray()
    src_array = ds.GetRasterBand(1).ReadAsArray()
    print "Applying mask..."
    cluster_array = src_array*mask_array
    print "Mask has been applied."

    # Create the masked geotiff and save to disk
    geo = ds.GetGeoTransform()
    masked_name = cut_name[:-4] + '_masked.tif'
    mask_ds = gdal.GetDriverByName('GTiff').Create(masked_name, ds.RasterXSize, ds.RasterYSize, gdal.GDT_Byte)
    mask_ds.SetGeoTransform((geo[0], geo[1], geo[2], geo[3], geo[4], geo[5]))
    mask_ds.GetRasterBand(1).WriteArray(cluster_array)

    # Threshold image
    print "Thresholding image..."
    thresh_array = Threshold(cluster_array,thresh_value)
    print "Thresholding done."

    # Save thresholded image to disk
    final_name = save_path + '/' + filename[:-4] + '_f.TIF'
    threshold_ds = gdal.GetDriverByName('GTiff').Create(final_name, ds.RasterXSize, ds.RasterYSize, gdal.GDT_Byte)
    threshold_ds.SetGeoTransform((geo[0], geo[1], geo[2], geo[3], geo[4], geo[5]))
    threshold_ds.SetProjection(ds.GetProjection())
    threshold_ds.GetRasterBand(1).WriteArray(thresh_array)

    # Close all files because it's good programming practice :)
    threshold_ds = None
    mask_ds = None
    ds = None

    cmd = 'rm -rf ' + cloud_name + ' ' + cut_name + ' ' + masked_name
    os.system(cmd)
##
##    # Use numpy's label function to cluster pixels
##    label_im, nb_labels = ndimage.label(thresh_array)
##    print "# clusters = ", nb_labels
##
##    # find_objects returns slices of array that contain each cluster
##    iceberg_list = ndimage.find_objects(label_im)
##
##    return iceberg_list

        


####### MAIN #######

if len(sys.argv) != 2:
    print "Wrong input!"
    exit()
    
path = sys.argv[1]
thresh_value = int(raw_input("Enter ice threshold value: "))

if path[-1] == '/':
    path = path[:-1]

save_path = path + '/' + 'Processed_Images/'
cmd = 'mkdir ' + save_path
os.system(cmd)

ProcessFolder(path, thresh_value, save_path)
StitchImages(save_path)


# Go through the clusters and see which ones have more then 1 pixel in them
##count = 0
##for x in iceberg_list:
##    if label_im[x].size > 1:
##        count = count + 1
##
##print count, " icebergs with size larger than 1."
##
##print "Shape = ", thresh_array.shape



