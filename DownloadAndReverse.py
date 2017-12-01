import vUtils
import os
import sys

print(sys.argv)
print(vUtils.getCurDir())

vUtils.changePts(sys.argv[1], 0.5, "slow")

if (sys.argv[1] == '-rev'):
    print(sys.argv[2])
    print(vUtils.getFilePath(sys.argv[2]))
    vUtils.reverseLongVideo(sys.argv[2])
else:
    vUtils.execYoutubedl('"'+sys.argv[1]+'" --exec "'+__file__+' -rev {}" ')



