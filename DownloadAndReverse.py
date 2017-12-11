from vUtils import *
import os
import sys

##concat=ConcatFilter()
##concat.addMedia('vinheta2.mp4')
##concat.addMedia('downloads\\rev_WORST Natural Disasters  Caught on Camera Hurricane, Tornado, Sandstorm, Hailstorm.mkv')
##concat.addMedia('downloads\\vfstWORST Natural Disasters  Caught on Camera Hurricane, Tornado, Sandstorm, Hailstorm.mkv')
##output='downloads\\Vid_WORST Natural Disasters  Caught on Camera Hurricane, Tornado, Sandstorm, Hailstorm.mkv'
##concat.addFilterToAll('fps=fps=60,scale=1600x900,setdar=16/9')
##params=concat.getFilterString(output)
##print(params)
##execFfmpeg(params)
##sys.exit()

def writeLog(text):
    file  = open('DownloadAndReverse.log', 'a')
    file.write(text+'\n')
    file.close()

vinheta='vinheta2.mp4'
downPath='downloads'

def conatMedias(medias, output):
    concat=ConcatFilter()
    for m in medias:
        concat.addMedia(m)

    concat.addFilterToAll('fps=fps=60,scale=1600x900,setdar=16/9')
    params=concat.getFilterString(output)
    execFfmpeg(params)

def reverseAndConcat(video, output):
    print(video)
    
    writeLog('reversing and concating video:' +video)
    tmpFolder=getTempFolder(output)
    fast=tmpFolder+'fast_'+getFileName(output)

    writeLog('changing pts: '+fast)
    changePts(video, 0.75, fast)
    reversed=tmpFolder+'rev_'+getFileName(output)
    
    writeLog('reversing: '+reversed)
    reverseLongVideo(fast, reversed)
    veryfast=tmpFolder+'vfst_'+getFileName(output)
    
    writeLog('acelerating: '+veryfast)
    changePts(fast, 0.75, veryfast) 
    videos=[]
    videos.append(vinheta)   
    videos.append(reversed)    
    videos.append(veryfast)
    writeLog('concatenating videos: '+output)
    conatMedias(videos, output)

    if os.path.isfile(output):
        shutil.rmtree(tmpFolder)

## C:\Users\Marcelo\Desktop\youtube\Scripts\DownloadAndReverse.py -revlist "downloads"
def revcatList(path):
    writeLog('Processing path '+path)
    files = [f for f in os.listdir(path) if (os.path.isfile(os.path.join(path, f)) and (os.path.splitext(f)[1].lower() in ['.mkv', '.mp4']))]
    sort_nicely(files, reverse=True)

    writeLog('Files found: '+','.join(files))    
    
    for f in files:
        video=os.path.join(path, f)
        output='output\\Vid_'+getFileName(video)
        if (os.path.isfile(output)):
            continue
        
        reverseAndConcat(video, output)

def downloadList(list):
    writeLog('downloading list '+list)
    with open(list) as f:
        lines = f.read().splitlines()

    for l in lines:
        if (os.path.isfile(l)):
            continue

        writeLog('downloading '+l)
        execYoutubedl(' -o "'+downPath+'//%(title)s.%(ext)s" "'+l+'"')      

if (sys.argv[1] == '-rev'):
    reverseAndConcat(sys.argv[2], 'output\\Vid_'+getFileName(video))    
elif (sys.argv[1] == '-revlist'):
    revcatList(sys.argv[2])    
elif (sys.argv[1] == '-dl'):
    execYoutubedl('"'+sys.argv[2]+'" ')
elif (sys.argv[1] == '-dlist'):
    downloadList(sys.argv[2])
else:
    execYoutubedl(' -o "'+downPath+'//%(title)s.%(ext)s" "'+sys.argv[1]+'" --exec "'+__file__+' -rev {}" ')



