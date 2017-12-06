import vUtils
import os
import sys

print(sys.argv)
print(vUtils.getCurDir())
videos=[]
videos.append('vinheta2.mp4')    
videos.append('output\\rev_Nature Beautiful short video 720p HD-668nUCeBHyY.mp4')    
videos.append('output\\vfstNature Beautiful short video 720p HD-668nUCeBHyY.mp4')
vUtils.concatFiles(videos, 'output\\Vid_123.mp4')

if (sys.argv[1] == '-rev'):
    video=vUtils.moveToFolder(sys.argv[2], 'output')
    print(video)
    reversed=vUtils.reverseLongVideo(video)
    video=vUtils.changePts(video, 0.5, 'vfst') 
    videos=[]
    videos.append('vinheta2.mp4')    
    videos.append(reversed)    
    videos.append(video)
    vUtils.concatFiles(videos, 'output\\Vid_'+vUtils.getFileName(video))
else:
    vUtils.execYoutubedl('"'+sys.argv[1]+'" --exec "'+__file__+' -rev {}" ')



