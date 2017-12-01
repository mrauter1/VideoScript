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

def getCurDir():
    return os.path.dirname(os.path.realpath(__file__))    

def shellExec(cmd, printCmd=True):
    p = Popen(cmd, shell=True)
    stdout, stderr = p.communicate()
    if printCmd:
        print(cmd)  
	
def getFfprobe():
	return '"'+getCurDir()+'\\..\\ffprobe.exe" '	
	
def shellExecOutput(cmd):
        import subprocess
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        return process.stdout

def getFfmpeg():
	return '"'+getCurDir()+'\\..\\ffmpeg.exe" '
	
def execFFprobe(params):
	shellExec(getFfprobe()+params)
	
def execFfmpeg(params):
	shellExec(getFfmpeg()+params)

def execYoutubedl(params):
	shellExec('"'+getCurDir()+'\\..\\youtube-dl.exe" '+params)    

def getDuration(video):
	retorno = shellExecOutput(getFfprobe()+' -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{0}"'.format(video))
	return float(retorno.readline().decode('UTF-8').strip())

def getExt(file):
        return os.path.splitext(file)[1].lower()

def getFileName(file, comExtensao=True):
        if (comExtensao):
            return os.path.basename(file)
        else:
            return os.path.splitext(os.path.basename(file))[0] 

def getFilePath(file):
       # return os.path.dirname(file)+'\\'
        return os.path.dirname(os.path.abspath(file))+'\\'

	
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

def changePts(file, pts):
    params = '-i "{input}" -filter:v "setpts={pts}*PTS" "{output}" '.format(input=file, pts=pts, output=file)
    execFfmpeg(params)
    return file
  
def reverse(file, prefix='rev_', removeOriginal=True):   
        video=getFileName(file)

        if (prefix!='') & (video.startswith(prefix)):
            return file
        
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

def concatFilesDirect(files, output):
        inputVideos= ''

        for f in files:
                inputVideos = inputVideos+' -i "'+f+'"'
                
        params=inputVideos+' -filter_complex "concat=n={len}:v=1:a=0 [v]" -map "[v]"  "{output}"'.format(len=len(files), output=output)
        execFfmpeg(params)

def concatFiles(files, output):
        listName='tmp'+getFileName(output, False)+'.txt'
        if isfile(listName):
            os.remove(listName)

        thefile = open(listName, 'w+')
            
        for item in files:
            thefile.write("file '%s'\n" % item)

        thefile.close()

#        params=' -i "{inputList}" -filter_complex "concat=n={len}:v=1:a=0 [v]" -map "[v]"  "{output}"'.format(inputList=listName, len=len(files), output=output)
        params='-f concat -safe 0 -i "{inputList}" "{output}"'.format(inputList=listName, output=output)
        execFfmpeg(params)
        
        if isfile(listName):
            os.remove(listName)

def moveToFolder(video, Folder='output'):
    if (Folder == ""):
        return video

    if not os.path.exists(Folder):
        os.makedirs(Folder)

    newVideo=Folder+"\\"+getFileName(video)
    if isfile(newVideo):
         os.remove(newVideo)
         
    os.rename(video, newVideo)
    return newVideo

def reverseLongVideo(video, MoveToFolder='output'):
        if "'" in video:
            newVideo=video.replace("'", "")
            if isfile(newVideo):
                os.remove(newVideo)   
            os.rename(video,newVideo)
            video=newVideo
            
        video=moveToFolder(video, MoveToFolder)

        folder=getFilePath(video)+os.path.splitext(getFileName(video))[0]+'tmp\\'
        if not os.path.exists(folder):
                os.makedirs(folder)

        listVideos=[]
        num=splitVideoKeyFrames(video, folder+'out')
        files = [f for f in listdir(folder) if (isfile(join(folder, f)) and (os.path.splitext(f)[1].lower() in [getExt(video)]))]
        sort_nicely(files, reverse=True)
        for f in files:
                file=folder+f
                fileRev=reverse(file)
                changePts(file, 2.0)
                listVideos.append(fileRev)

        output=getFilePath(video)+'rev_'+getFileName(video)
        concatFiles(listVideos, output)

        if (os.path.isfile(output)):
                shutil.rmtree(folder)
	    

		
