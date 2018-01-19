from vUtils import *
import os
import sys

import time
from random import shuffle
from nose.util import getfilename

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
    file.write(time.strftime("%H:%M:%S: ")+text+'\n')
    file.close()

# from inspect import getmembers
# from pprint import pprint

def dump(obj):
  '''return a printable representation of an object for debugging'''
  newobj=obj
  if '__dict__' in dir(obj):
    newobj=obj.__dict__
    if ' object at ' in str(obj) and not newobj.has_key('__type__'):
      newobj['__type__']=str(obj)
    for attr in newobj:
      newobj[attr]=dump(newobj[attr])
  return newobj

vinheta = 'vinheta2.mp4'
downPath = 'downloads'

def concatMedias2(medias, output):
    f=Filters()
    
    labels=[]
    
    for m in medias:    
        media = f.newMediaInput(m)
        f.addInput(media)
        v = f.vFilter(media.vLabel, 'fps=fps=60,scale=1600x900,setdar=16/9')     
        labels.append(v.Label)
        labels.append(media.aLabel)                
       
    c = f.concat(labels)
    
    f.changePts(c.vOutLabel, c.aOutLabel, 0.5)

    writeLog('concatenating videos: ' + output)
    print(f.getCmdLine(output))
    execFfmpeg(f.getCmdLine(output))    

def addMusicsToVideos(videoList, audioPath, concat):
    writeLog('Adding music to video. Audio path: '+audioPath)
    videoTime=0
    for v in videoList:
        videoTime = videoTime + getDuration(v)

    totalAudioTime = 0

    files = [f for f in os.listdir(audioPath) if (os.path.isfile(os.path.join(audioPath, f)) and (os.path.splitext(f)[1].lower() in ['.mp3']))]
    shuffle(files)

    for f in files:
        audio = os.path.join(audioPath, f)
        aduration=getDuration(audio)
        totalAudioTime = totalAudioTime+aduration
        m=concat.addMedia(audio, True, False)
        if (totalAudioTime >= videoTime):
            end=aduration-(totalAudioTime-videoTime)
            b=Block()
            b.Filter='atrim=0:'+str(end)
            m.addAudioFilter(b)
            break

def reverseAndConcat(video, output):
    print(video)
    
    tmpFolder=getTempFolder(output)

    reversed=tmpFolder+'reversed.mkv'
       
    reencode(vinheta)
    #newVideo=tmpFolder+getFileName(video)
    reencode(video)
    #video=newVideo
    
    writeLog('reversing: '+reversed)
    reverseLongVideo(video, reversed)

    f=Filters()

    vin=f.newMediaInput(vinheta)
    rev=f.newMediaInput(reversed)
    vid=f.newMediaInput(video)
#    f.normalizeInputs('fps=fps=60,scale=1600x900,setdar=16/9,settb=AVTB,fifo', 'asettb=AVTB, afifo')
    
    v1, a1 = f.changePts(rev.vLabel, rev.aLabel, 0.75)
    v2, a2 = f.changePts(vid.vLabel, vid.aLabel, 0.5)
    
    labels=[]
    labels.append(vin.vLabel)
    labels.append(vin.aLabel)
    labels.append(v1.Label)
    labels.append(a1.Label)
    labels.append(v2.Label)
    labels.append(a2.Label)                  
       
    c = f.concat(labels)

    writeLog('concatenating videos: ' + output)
    writeLog(f.getCmdLine(output))
    print(f.getCmdLine(output))
    
    execFfmpeg(f.getCmdLine(output))        

    try:
        if os.path.isfile(output):
            shutil.rmtree(tmpFolder)
    except:
        print("Erro ao deletar a pasta temporaria")           

def reverseAndConcat2(video, output):
    print(video)
    
    writeLog('reversing and concating video:' +video)
    tmpFolder=getTempFolder(output)
    fast=tmpFolder+'fast_'+getFileName(output)
    
    #convertCodec(vinheta, getFileName(vinheta,False)+'.'+getExt(vinheta))

    writeLog('changing pts: '+fast)
#    changePts(video, 0.75, fast)
    
    reversed=tmpFolder+'rev_'+getFileName(output) 
    writeLog('reversing: '+reversed)   
#    reverseLongVideo(fast, reversed)
    
    veryfast=tmpFolder+'vfst_'+getFileName(output)  
    writeLog('acelerating: '+veryfast)  
#    changePts(fast, 0.75, veryfast) 
        
    out1=tmpFolder+'out1_'+getFileName(output)     
        
    writeLog('concatenating videos: '+out1)    
    concat=ConcatFilter()
    concat.mapParameters=' -y'    
    r=concat.addMedia(reversed, False)
    f=concat.addMedia(veryfast, False)
    addMusicsToVideos([reversed,veryfast], '..//audio//', concat)
    #revvideo=tmpFolder+'final'

    #print(concat.getFilterString(out1))
    
    #execFfmpeg(concat.getFilterString(out1))
    
    concatlist = []
    concatlist.append(vinheta)
    concatlist.append(reversed)
    concatlist.append(veryfast)
    concatFiles(concatlist, output, True, True)
        
#     concat=ConcatFilter()
#     concat.mapParameters=' -y'
#     concat.addMedia(vinheta)
#     concat.addMedia(out1) 
#     execFfmpeg(concat.getFilterString(out1))    
        
##    if os.path.isfile(output):
##        shutil.rmtree(tmpFolder)

def revcatList(path):
    writeLog('Processing path ' + path)
    files = [f for f in os.listdir(path) if (os.path.isfile(os.path.join(path, f)) and (os.path.splitext(f)[1].lower() in ['.mkv', '.mp4']))]
    sort_nicely(files, reverse=True)

    writeLog('Files found: ' + ','.join(files))    
    
    for f in files:
        video = os.path.join(path, f)
        output = 'output\\Vid_' + getFileName(video)
        if (os.path.isfile(output)):
            continue
        
        reverseAndConcat(video, output)


def downloadList(list):
    writeLog('downloading list ' + list)
    with open(list) as f:
        lines = f.read().splitlines()

    for l in lines:
        if (os.path.isfile(l)):
            continue

        writeLog('downloading '+l)
        execYoutubedl(' -o "'+downPath+'//%(title)s.%(ext)s" "'+l+'"')      

#addMusicsToVideo('science1.mkv', '..//audio//', 'sc2.mkv')
#reverseAndConcat('science1.mkv', 'sc2.mkv')

reverseAndConcat('WhatsApp Video.mp4', 'test1.mp4')

#reverseAndConcat2('WhatsApp Video.mp4', 'tout.mp4')

m = []
m.append(vinheta)
m.append('science1.mkv')
m.append('sc2.mkv')
# concatMedias2(m, 'out.mp4')

if (len(sys.argv) > 1):
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