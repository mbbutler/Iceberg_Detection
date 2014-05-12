import sys

if len(sys.argv) != 3:
    print "Usage is: python intersect.py [file1] [file2]"
    exit(0)


fname1 = sys.argv[1]
fname2 = sys.argv[2]

fn1 = open(fname1, 'r')
fn2 = open(fname2, 'r')
output = open(fname1[-20:-13] + '_intersected.txt', 'w')

for line1 in fn1:
    fn2.seek(0,0)
    for line2 in fn2:
        if line1 == line2:
            output.write(line1)
            break

fn1.close()
fn2.close()
output.close()
