from vUtils import *
import os
import sys
import ffmpeg
from inspect import getmembers
from pprint import pprint

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

def writeLog(text):
    file = open('DownloadAndReverse.log', 'a')
    file.write(text + '\n')
    file.close()


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

def reverseAndConcat(video, output):
    print(video)
    
    writeLog('reversing and concating video:' + video)
    tmpFolder = getTempFolder(output)
    fast = tmpFolder + 'fast_' + getFileName(output)

    writeLog('changing pts: ' + fast)
    changePts(video, 0.75, fast)
    reversed = tmpFolder + 'rev_' + getFileName(output)
    
    writeLog('reversing: ' + reversed)
    reverseLongVideo(fast, reversed)
    veryfast = tmpFolder + 'vfst_' + getFileName(output)
    
    writeLog('acelerating: ' + veryfast)
    changePts(fast, 0.75, veryfast) 
	
    #concat = ConcatFilter()


# #    if os.path.isfile(output):
# #        shutil.rmtree(tmpFolder)


# # C:\Users\Marcelo\Desktop\youtube\Scripts\DownloadAndReverse.py -revlist "downloads"
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

        writeLog('downloading ' + l)
        execYoutubedl(' -o "' + downPath + '//%(title)s.%(ext)s" "' + l + '"')      


#split = ffmpeg.input(vinheta).filter_multi_output('split')
#split0 = split.stream(0)
#split1 = split[1]
#ffmpeg.concat(split0, split1).output('vinout.mp4').run()

m = []
m.append(vinheta)
m.append('video_withaudio.mp4')
m.append('WhatsApp Video.mp4')
concatMedias2(m, 'C:\\Videos\\Scripts\\out.mp4')

if (len(sys.argv) > 1):
    if (sys.argv[1] == '-rev'):
        reverseAndConcat(sys.argv[2], 'output\\Vid_' + getFileName(sys.argv[2]))    
    elif (sys.argv[1] == '-revlist'):
        revcatList(sys.argv[2])    
    elif (sys.argv[1] == '-dl'):
        execYoutubedl('"' + sys.argv[2] + '" ')
    elif (sys.argv[1] == '-dlist'):
        downloadList(sys.argv[2])
    else:
        execYoutubedl(' -o "' + downPath + '//%(title)s.%(ext)s" "' + sys.argv[1] + '" --exec "' + __file__ + ' -rev {}" ')

