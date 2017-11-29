from subprocess import Popen
import sys
import os 
from os import rename, listdir
from os.path import isfile, join
import re
import shutil

def tryint(s):
    try:
        return int(s)
    except:
        return s

def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [ tryint(c) for c in re.split('([0-9]+)', s) ]

def sort_nicely(l, reverse=False):
    """ Sort the given list in the way that humans expect.
    """
    l.sort(key=alphanum_key, reverse=reverse)

def shellExec(cmd):
	p = Popen(cmd, shell=True)
	stdout, stderr = p.communicate()	
	print(cmd)  
	
def getFfprobe():
	return '"'+dir_path+'\\..\\ffprobe.exe" '	
	
def shellExecOutput(cmd):
        import subprocess
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
#	stdout = process.communicate()[0]
        return process.stdout

def getFfmpeg():
	return '"'+dir_path+'\\..\\ffmpeg.exe" '
	
def execFFprobe(params):
	shellExec(getFfprobe()+params)
	
def execFfmpeg(params):
	shellExec(getFfmpeg()+params)

def getDuration(video):
	retorno = shellExecOutput(getFfprobe()+' -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{0}"'.format(video))
	return float(retorno.readline().decode('UTF-8').strip())

def getExt(file):
        return os.path.splitext(file)[1].lower()

def getFileName(file):
        return os.path.basename(file)

def getFilePath(file):
        return os.path.dirname(file)+'\\'
       # return os.path.dirname(os.path.abspath(file))+'\\'

	
def doFadeInFadeOut(video):
  if ("fifo_" in video):
	  return video
	  
  newVid = 'fifo_'+video   
  params = '-i {0} -sseof -1 -copyts -i {0} -filter_complex "[1]fade=out:0:10[t];[0][t]overlay,fade=in:0:30[v]" '.format(video)  
  params=params+'-map "[v]" -c:v libx264 -crf 22 -preset veryfast -shortest {1}'.format(video, newVid)  
# fade with audio  
#  params = '-i {0} -sseof -1 -copyts -i {0} -filter_complex "[1]fade=out:0:10[t];[0][t]overlay,fade=in:0:30[v]; anullsrc,atrim=0:2[at];'.format(video)
#  params=params+'[0][at]acrossfade=d=1,afade=d=1[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 22 -preset veryfast -shortest {1}'.format(video, newVid)
  execFfmpeg(params)
  
  rename(video, video+'.bkp')
  return newVid	  
  
def reverseVideo(file, prefix='rev_', removeOriginal=True):
        video=getFileName(file)
        
        if (prefix==''):
                newVideo=getFilePath(file)+'tmp'+video
        else:        
                newVideo = getFilePath(file)+prefix+video
                
        params = '-i "{0}" -vf reverse -af areverse "{1}" '.format(file, newVideo)  
  
        execFfmpeg(params) 
  
        if (os.path.isfile(newVideo)) & (removeOriginal): 
                os.remove(file) 

        if (prefix==''):
                os.rename(newVideo, file)
                
        return newVideo
		
def splitVideo(video, tempoVideo=4, outputPrefix='vid'):
        duration = getDuration(video)
        start=0
        end=tempoVideo
        num=1
        while (start < duration):
                nomeVideo=outputPrefix+str(num)+getExt(video)
                params = '-ss {start} -t {end} -i "{input}" -c copy "{output}" '.format(input=video, start=start, end=tempoVideo, output=nomeVideo)
                execFfmpeg(params) 
                start=end
                end=start+tempoVideo
                num+=1
	
        return

def splitVideoKeyFrames(video, outputPrefix='out'):
        execFfmpeg('-i "{input}" -acodec copy -f segment -vcodec copy -reset_timestamps 1 -map 0 "{prefix}%d{ext}"'.format(input=video, prefix=outputPrefix,ext=getExt(video)))

def concatFiles(files, output):
        inputVideos= ''

        for f in files:
                inputVideos = 'inputVideos -i "'+f+'"'

        params=inputVideos+' -filter_complex "concat=n={len}:v=1:a=0 [v]" -map "[v]"  "{output}"'.format(len=len(files), output=output)
        execFfmpeg(params)    

def reverseLongVideo(video):
        folder=getFilePath(video)+os.path.splitext(getFileName(video))[0]+'tmp\\'
        if not os.path.exists(folder):
                os.makedirs(folder)

        listConcat=[]
        num=splitVideoKeyFrames(video, folder+'out')
        files = [f for f in listdir(folder) if (isfile(join(folder, f)) and (os.path.splitext(f)[1].lower() in [getExt(video)]))]
        sort_nicely(files, reverse=True)
        for f in files:
                file=folder+f
                fileRev=reverseVideo(file)                
                listConcat.append(fileRev)

        output=getFilePath(video)+'rev_'+getFileName(video)
        concatFiles(listConcat, output)

        if (os.path.isfile(output)):
                shutil.rmtree(folder)
		
dir_path = os.path.dirname(os.path.realpath(__file__))

f=sys.argv[1]

reverseLongVideo(sys.argv[1])

#splitVideo(sys.argv[1])
#shellExec('"'+dir_path+'\\..\\youtube-dl.exe" -o "%(title)s%(id)s.%(ext)s" "'+sys.argv[1]+'" '.format())	 

#files = [f for f in listdir(dir_path) if (isfile(join(dir_path, f)) and (os.path.splitext(f)[1].lower() in ['.webm', '.mkv', '.mp4']))]

#files.sort()

#for f in files:
#  newVid=''
#  newVid=reverseVideo(f)
		
