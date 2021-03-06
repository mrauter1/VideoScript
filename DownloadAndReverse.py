from vUtils import *
import os
import sys
import datetime

import time
from random import shuffle
from nose.util import getfilename
from win32con import CDM_GETFILEPATH

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
    print(text)
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
downPath = 'downloads\\'

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

def reverseAndConcat(video, output, trimstart='', trimend='', revpts=0.75, normalpts=0.5):
    writeLog('Iniciando reverseAndConcat do video: '+video)
    
    tmpFolder=getTempFolder(output)
       
    #reencode(vinheta)

    processed=tmpFolder+'processed'+getExt(video) 
    writeLog('preProcessing video: '+processed)
    preProcessVideo(video, processed, '-c:v copy -c:a copy -y', trimstart, trimend)

    reversed=tmpFolder+'reversed'+getExt(video)    
    writeLog('reversing: '+reversed)
    reverseLongVideo(processed, reversed, '')

    f=Filters()
    rev=f.newMediaInput(reversed)
    vid=f.newMediaInput(processed)
    
    v1, a1 = f.changePts(rev.vLabel, rev.aLabel, revpts)
    v2, a2 = f.changePts(vid.vLabel, vid.aLabel, normalpts)
         
    c = f.concat([v1.Label, a1.Label, v2.Label, a2.Label], v=1, a=1)
    
    conc1=tmpFolder+'conc1'+getExt(video) 
    writeLog('concatenating videos: ' + conc1)

    writeLog(f.getCmdLine(conc1))      
    execFfmpeg(f.getCmdLine(conc1))
    
    comMusica=tmpFolder+'comMusica'+getExt(conc1)    
    addMusicsToVideo(conc1, '//audio//', comMusica)

    writeLog('finishing video: ' + output)
    concatFiles([vinheta, comMusica], output)
    
    try:
        if os.path.isfile(output):
            shutil.rmtree(tmpFolder)
    except:
        writeLog('Erro ao deletar a pasta temporaria')           

def getOutputDir():
    ##return vUtils.getCurDir()+'\\output\\'
    return 'output\\'

def revcatList(path):
    writeLog('Processing path ' + path)
    files = [f for f in os.listdir(path) if (os.path.isfile(os.path.join(path, f)) and (os.path.splitext(f)[1].lower() in ['.mkv', '.mp4']))]
    sort_nicely(files, reverse=True)

    writeLog('Files found: ' + ','.join(files))    
    
    for f in files:
        video = os.path.join(path, f)
        output = getOutputDir()+'RV' + getFileName(video)[:10]
        if (os.path.isfile(output)):
            continue
        
        try:
            reverseAndConcat(video, output)
        except:
            writeLog('Erro ao criar video: '+output)   
            
def downloadAndProcessVideos(fileList):    
    def getValue(name, default):
        index=l.find('['+name+'=')
        if index>=0:
            stId=index+len('['+name+'=')
            return l[stId:l.find(']',index)]
        else:
            return default               
    
    with open(fileList) as f:
        lines = f.read().splitlines()
        
    for l in lines:
        try:
            index=l.find(' ')
            if index<=0:
                index=len(l)
                
            url= l[0:index]
            
            trimstart=getValue('start', '')
            trimend=getValue('end', '')
            name=getValue('name', '')
            revpts=getValue('revpts', '0.75')
            normalpts=getValue('revpts', '0.5')
            
#             print(url)
#             print(trimstart)
#             print(trimend)
#             print(name)
#             print(revpts)

            fileName=execYoutubedl(' -o "%(title)s.%(ext)s" --get-filename --merge-output-format mp4 "'+url+'"', True)
            if name:        
                fileName=downPath+name+getExt(fileName)
            else:
                fileName=downPath+getFileName(fileName[0:25], False)+getExt(fileName)      

            writeLog('Iniciando o processamento da url: '+url)
            
            writeLog(fileName)
                                
            execYoutubedl(' -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4" -o "'+fileName+'" "'+url+'" --merge-output-format mp4 --exec "lastdownload.bat {}" ')                       
            if not isfile(fileName):
                fileName = getFilePath(fileName)+getFileName(fileName)+'.mkv'

            if not isfile(fileName):
                raise Exception("Video não encontrado! Url: "+url+", nome arquivo: "+fileName)
                      
            output=getOutputDir()+getFileName(fileName[0:25], False)+getExt(fileName)                        
            writeLog('iniciando processamento no arquivo: '+fileName+', output: '+output)
            reverseAndConcat(fileName, output, trimstart, trimend)
            writeLog('finalizado processamento do arquivo: '+output)
        except Exception as err:
            try:
                writeLog('Erro ao processar url: '+url+' Erro: '+str(err))
            except:
                print('Erro')        

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

print("iniciando")
downloadAndProcessVideos('Videos.txt')
#reverseAndConcat('\\Surf fails caixote.mp4', 'Surf Fails.mp4', '00:00:38', '00:01:08')

#reverseAndConcat('WhatsApp Video.mp4', 'test1.mp4')

#print(getDuration('C:\\Videos\\output\\20 Amazing Science Experitmp\\reversed.mp4'))

if (len(sys.argv) > 1):
    if (sys.argv[1] == '-rev'):
        reverseAndConcat(sys.argv[2], getOutputDir()+'Vid_'+getFileName(video))    
    elif (sys.argv[1] == '-revlist'):
        revcatList(sys.argv[2])    
    elif (sys.argv[1] == '-dl'):
        execYoutubedl('"'+sys.argv[2]+'" ')
    elif (sys.argv[1] == '-dlist'):
        downloadList(sys.argv[2])
    else:
        execYoutubedl(' -o "'+downPath+'//%(title)s.%(ext)s" "'+sys.argv[1]+'" --exec "'+__file__+' -rev {}" ')