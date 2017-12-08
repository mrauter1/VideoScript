import vUtils
import os
import sys


##concat.addMedia('vinheta2.mp4')
##concat.addMedia('output\\rev_Nature Beautiful short video 720p HD-668nUCeBHyY.mp4')
##concat.addMedia('output\\vfstNature Beautiful short video 720p HD-668nUCeBHyY.mp4')
##concat.addFilterToAll('fps=fps=60,scale=1600x900,setdar=16/9')
##params=concat.getFilterString('output.mp4')
##print(params)
##vUtils.execFfmpeg(params)
##sys.exit()

def conatMedias(medias, output):
    concat=vUtils.ConcatFilter()
    for m in medias:
        concat.addMedia(m)

    concat.addFilterToAll('fps=fps=60,scale=1600x900,setdar=16/9')
    params=concat.getFilterString(output)
    vUtils.execFfmpeg(params)

if (sys.argv[1] == '-rev'):
    video=vUtils.moveToFolder(sys.argv[2], 'output')
    print(video)
    reversed=vUtils.reverseLongVideo(video)
    video=vUtils.changePts(video, 0.5, 'vfst') 
    videos=[]
    videos.append('vinheta2.mp4')    
    videos.append(reversed)    
    videos.append(video)
    conatMedias(videos, 'output\\Vid_'+vUtils.getFileName(video))
else:
    vUtils.execYoutubedl('"'+sys.argv[1]+'" --exec "'+__file__+' -rev {}" ')



