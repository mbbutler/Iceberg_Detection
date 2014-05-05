import os

def MergeImages(img1, img2, new_name):
    cmd = "gdal_merge.py -o " + new_name + " -ot Byte " + img1 + " " + img2
    os.system(cmd)


############ MAIN ############

if sys.argc != 2:
    print "Wrong input!"
    exit()
    
path = sys.argv[1]

if path[-1] != '/':
    path += '/'

save_path = path + 'Combined_Images/'

cmd = 'mkdir ' + save_path
os.system(cmd)

files = []
for (dirpath, dirname, filename) in os.walk(path):
    files.extend(filename)

print files
while files:
    fn = files[0]
    if len(files) == 1:
        cmd = 'mv ' + path + fn + ' ' + save_path + fn[9:16] + '.TIF'
        print cmd
        os.system(cmd)
    else:
        isStitched = False
        for ofn in files[1:]:
            if fn[9:16] in ofn:
                MergeImages(path + fn, path + ofn, save_path + fn[9:16] + '.TIF')
                cmd = 'mv ' + path + fn[9:16] + '.TIF' + ' ' + save_path + fn[9:16] + '.TIF'
                os.system(cmd)
                cmd = 'rm -rf ' + path + fn + ' ' + path + ofn
                os.system(cmd)
                isSitched = True
        if not isStitched:
            cmd = 'mv ' + path + fn + ' ' + save_path + fn[9:16] + '.TIF'
            os.system(cmd)

    files = []
    for (dirpath, dirname, filename) in os.walk(path):
        files.extend(filename)
            
        
        
    
