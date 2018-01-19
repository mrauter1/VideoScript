from vUtils import *
import os
import sys
import datetime

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
        
def addMusicsToVideo(video, audioPath, output):
    writeLog('Adding music to video. Audio path: '+audioPath)
    videoTime=0
    videoTime = getDuration(video)

    totalAudioTime = 0

    audios = [f for f in os.listdir(audioPath) if (os.path.isfile(os.path.join(audioPath, f)) and (os.path.splitext(f)[1].lower() in ['.mp3']))]
    shuffle(audios)
    
    f = Filters() 
    
    f.newMediaInput(video)
    
    labels = []

    for a in audios:
        audio = os.path.join(audioPath, a)
        aduration=getDuration(audio)
        totalAudioTime = totalAudioTime+aduration
        m=f.newMediaInput(audio)     
        f.audioFilterMedia(m, 'adelay=1500')              
        
        if (totalAudioTime >= videoTime):
            end=aduration-(totalAudioTime-videoTime)
            f.audioFilterMedia(m, 'atrim=0:'+str(end))
            
        labels.append(m.aLabel)
        
        if (totalAudioTime >= videoTime):
            break            

    if len(labels) > 1:       
        f.concat(labels, 0, 1)
    
    if f.lastAudioLabelNum == 0:
        f.aMap='1:a'
    
    f.outOptions='-c:v copy -c:a aac -b:a 192k -ac 2 -video_track_timescale 60000 -ar 48000 -y '
    
    print(f.getCmdLine(output))
    
    execFfmpeg(f.getCmdLine(output))  
        
def preProcessVideo(video, newOutput, outOptions='', trimstart='', trimend=''):
    if newOutput:
        newFile=newOutput
    else:
        newFile=addPrefix(file, 'tmp')
           
    f=Filters()
    
    trimopt=''
    if (trimstart):
        trimopt='-ss '+trimstart
        
    if (trimend):
        trimopt=trimopt+' -to '+trimend
        
    if trimopt:
        trimopt=trimopt+' -async 1'       
        
    f.inOptions=trimopt     
                
    vid=f.newMediaInput(video)
            
#    f.vFilterMedia(vid, 'fps=fps=60,scale=1600x900,settb=AVTB')

    if f.outOptions:
        f.outOptions = outOptions

    print(f.getCmdLine(newFile))
    execFfmpeg(f.getCmdLine(newFile))
        
    if (newOutput=='') and (isfile(newFile)):
       os.remove(file)                      
       os.rename(newFile, file)                   

def reverseAndConcat(video, output):
    print(video)
    
    tmpFolder=getTempFolder(output)
       
    #reencode(vinheta)

    processed=tmpFolder+'processed'+getExt(video) 
    writeLog('preProcessing video: '+processed)
    preProcessVideo(video, processed, '-c:v copy -c:a copy -y', '', '')

    reversed=tmpFolder+'reversed'+getExt(video)    
    writeLog('reversing: '+reversed)
    reverseLongVideo(processed, reversed, '')

    f=Filters()
    rev=f.newMediaInput(reversed)
    vid=f.newMediaInput(processed)
    
    v1, a1 = f.changePts(rev.vLabel, rev.aLabel, 0.75)
    v2, a2 = f.changePts(vid.vLabel, vid.aLabel, 0.5)
         
    c = f.concat([v1.Label, a1.Label, v2.Label, a2.Label], v=1, a=1)
    
    conc1=tmpFolder+'conc1'+getExt(video) 
    writeLog('concatenating videos: ' + conc1)

    writeLog(f.getCmdLine(conc1))      
    execFfmpeg(f.getCmdLine(conc1))
    
    comMusica=tmpFolder+'comMusica'+getExt(conc1)    
    addMusicsToVideo(conc1, '..//audio//', comMusica)

    writeLog('concatenating videos: ' + output)
    concatFiles([vinheta, comMusica], output)
    
    try:
        print('nada')
        if os.path.isfile(output):
            shutil.rmtree(tmpFolder)
    except:
        writeLog('Erro ao deletar a pasta temporaria')           

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
        
        try:
            reverseAndConcat(video, output)
        except:
            writeLog('Erro ao criar video: '+output)   
             


def downloadList(list):
    writeLog('downloading list ' + list)
    with open(list) as f:
        lines = f.read().splitlines()

    for l in lines:
        if (os.path.isfile(l)):
            continue

        writeLog('downloading '+l)
        execYoutubedl(' -o "'+downPath+'//%(title)s.%(ext)s" "'+l+'"')      

#preProcessVideo('tout.mp4', 'testepre.mp4', '00:02:29', '00:02:31.99')

reverseAndConcat('..\\Nature Beautiful short video 720p HD.mp4', 'Nature Beautiful.mp4')

#reverseAndConcat('WhatsApp Video.mp4', 'test1.mp4')

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