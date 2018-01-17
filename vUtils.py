from subprocess import Popen
import sys
import os 
from os import rename, listdir
from os.path import isfile, join
import re
import shutil

def sameFile(file1, file2):
    if ((os.path.abspath(os.path.realpath(file1.upper()))) == (os.path.abspath(os.path.realpath(file2.upper())))):
        return True
    else:
        return False    
    
class Media:

    def __init__(self, mediaPath, inputNo):
        self.mediaPath=mediaPath
        self.vFilters=[]
        self.aFilters=[]
        self.hasAudio=True
        self.hasVideo=True

        self.vLabel='['+str(inputNo)+':v]'
        self.aLabel='['+str(inputNo)+':a]'        

    def addFilter(self, filter_):
        self.vFilters.append(filter_)
        self.vLabel=filter_.Label

    def addAudioFilter(self, filter_):
        self.aFilters.append(filter_)
        self.aLabel=filter_.Label
        
class Block:
    def __init__(self, origin=''):
        self.origin=origin
        self.Label = ''
        self.Filter = ''           

    def toStr(self):
        return '{origin}{filter}{label}'.format(
                  origin=self.origin,
                  filter=self.Filter,
                  label=self.Label)
               
class ConcatBlock(Media):
    def inLabelsStr(self):
        labels = ''
        for l in self.inLabels:
            labels = labels+l
            
        return labels        
                
    def __init__(self, inLabels, v, a, vOutLabel, aOutLabel):
        self.inLabels=inLabels
        self.vOutLabel=vOutLabel
        self.aOutLabel=aOutLabel
        self.v=v
        self.a=a                
            
        Block.__init__(self, self.inLabelsStr())     
        self.Label = vOutLabel+aOutLabel
        
    def toStr(self):
        n=len(self.inLabels) // (self.v+self.a)
                
        self.Filter='concat=n='+str(n)+':v='+str(self.v)+':a='+str(self.a)
        return Block.toStr(self)
            
class Filters:
    def __init__(self):
        self.blocks = []
        self.inputs = []
        self.inputBlock = dict()
        self.output = []
        self.lastVideoLabelNum = 0
        self.lastAudioLabelNum = 0
        self.inOptions=' -r 60'
        self.outOptions='-c:v libx264 -c:a aac -crf 23 -preset medium -vf -ac 2 -b:a 192k -f format=yuv420p ' 
        
    def lastVideoLabel(self):
        return '[v{0}]'.format(str(self.lastVideoLabelNum))            
        
    def lastAudioLabel(self):
        return '[a{0}]'.format(str(self.lastAudioLabelNum))        
        
    def nextVideoLabel(self):
        self.lastVideoLabelNum = self.lastVideoLabelNum+1
        return self.lastVideoLabel()
    
    def nextAudioLabel(self):
        self.lastAudioLabelNum = self.lastAudioLabelNum+1
        return self.lastAudioLabel()

    def newMediaInput(self, mediaPath):
        m = Media(mediaPath, len(self.inputs))
        self.addInput(m)
        return m
            
    def addInput(self, media):
        self.inputs.append(media)
                     
    
    def getInputLabel(self, media, tipo):
        #Tipo = v ou a
        return '[{0}:{1}]'.format(self.inputs.index(media), tipo)
        
    def vFilter(self, origin, filterStr):
        block = Block(None)
        block.origin = origin
        block.Label = self.nextVideoLabel()
        block.Filter = filterStr
        self.blocks.append(block)
        return block
    
    def aFilter(self, origin, filterStr):
        block = Block(None)
        block.origin=origin
        block.Label = self.nextAudioLabel()
        block.Filter = filterStr
        self.blocks.append(block)
        return block
    
    def vFilterMedia(self, media, filterStr):
        f = self.vFilter(media.vLabel, filterStr)
        media.addFilter(f)
        
    def aFilterMedia(self, media, filterStr):
        f = self.aFilter(media.vLabel, filterStr)
        media.addFilter(f)                               
    
    def concat(self, inLabels, v=1, a=1):
        block = ConcatBlock(inLabels, v, a,  self.nextVideoLabel(), self.nextAudioLabel())
        self.blocks.append(block)
        return block
    
    def changePts(self, vLabel, aLabel, pts):
        atempo=round(1.0/pts,3)            
        vBlock = self.vFilter(vLabel, 'setpts='+str(pts)+'*PTS')
        aBlock = self.aFilter(aLabel, 'atempo='+str("%.3f" % atempo))
        return vBlock, aBlock
   
    def getCmdLine(self, output):
        inputs = ''
        filters = ''
        cnt=0
        for m in self.inputs:
            inputs = inputs +' -i "'+m.mediaPath+'" '
            
        for b in self.blocks:       
            if filters:
                filters=filters+';'   
            filters = filters + b.toStr()

            cnt=cnt+1
            
        v=self.lastVideoLabel()
        a=self.lastAudioLabel()        

        return inputs +' '+self.inOptions+' -filter_complex "'+filters+'" -map "'+v+'" -map "'+a+'" '+self.outOptions+' '+output
        
class ConcatFilter:

    def __init__(self):
        self.audioFormat='aac'
        self.videoFormat='libx264'
        self.mapParameters = ''
        self.mediaList=[]
        self.videoContainerList=[]
        self.audioContainerList=[]

    def addMedia(self, mediaPath, hasAudio=True, hasVideo=True):
        media = Media(mediaPath, 0)
        media.hasAudio=hasAudio
        media.hasVideo=hasVideo
        self.mediaList.append(media)
        return media

    def addVFilter(self, mediaPath, filter):
        for m in self.mediaList():
            if sameFile(m.mediaPath, mediaPath):
                m.addVFilter(filter)
                return

        raise "addFilter: Media não encontrada!"

    def getLabel(self, prefix, cnt):
        m = self.mediaList[cnt]    
    
        if (prefix == 'v') and (m.hasVideo):
            if (len(m.vFilters) == 0):
                return '['+str(cnt)+':v]'
            else:   
                return '[v'+str(cnt)+']'

        if (prefix == 'a') and (m.hasAudio):
            if (len(m.aFilters) == 0):
                return '['+str(cnt)+':a]'
            else:
                return '[a'+str(cnt)+']'

        return ''

    

    def getFilterString(self, output):
        inputs = ''
        videoFilters = ''
        audioFilters = ''
        param2 = ''
        cnt=0
        videoCount=0
        for m in self.mediaList:
            inputs = inputs +' -i "'+m.mediaPath+'" '

            if m.hasVideo:
                videoCount=videoCount+1
                for v in m.vFilters:
                    videoFilters = videoFilters+'[{0}:v]{1}[v{0}];'.format(cnt, v)

            for a in m.aFilters:
                audioFilters = audioFilters+'[{0}:a]{1}[a{0}];'.format(cnt, a)

            videoLabel = self.getLabel('v', cnt)

            audioLabel = self.getLabel('a', cnt)
                
            param2 = param2+'{0}{1}'.format(videoLabel, audioLabel)

            cnt=cnt+1

        formatParameter = ((' -c:v {0}'.format(self.videoFormat) if self.videoFormat != '' else '') +
                          (' -c:a {0}'.format(self.audioFormat) if self.audioFormat != '' else ''))

        return (inputs +' -filter_complex "'+videoFilters+' '+audioFilters+' '+param2+' concat=n='+str(videoCount)+':v=1:a=1 [v][a]" -map "[v]" -map "[a]" '
                      +'{format} {mapPar} "{output}"'.format(format=formatParameter, mapPar=self.mapParameters, output=output))

    def addVFilterToAll(self, filter):
        for m in self.mediaList:
            m.addVFilter(filter)

    def addAFilterToAll(self, filter):
        for m in self.mediaList:
            m.addAFilter(filter)

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
	#return '"'+getCurDir()+'\\..\\ffmpeg.exe" '
    return "ffmpeg.exe "
	
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

def changePts(file, pts, output):
    atempo=round(1.0/pts,3)    
    #params = '-i "{input}" -r 60 -filter:v  "setpts={pts}*PTS" -y "{output}" '.format(input=file, pts=pts, output=newFile)
    params='-i "{input}" -r 60 -filter_complex "[0:v]setpts={pts}*PTS[v];[0:a]atempo={atempo}[a]" -map "[v]" -map "[a]" -y "{output}"'.format(input=file, pts=pts, atempo=atempo, output=output)
    execFfmpeg(params)
  
def reverse(file,output, removeOriginal=True):   
        params = '-i "{0}" -vf reverse -af areverse "{1}" '.format(file, output)  
  
        execFfmpeg(params) 
  
        if (os.path.isfile(output)) & (removeOriginal): 
            os.remove(file) 
		
def splitVideo(video, tempoVideo=4, outputPrefix='vid'):
        duration = getDuration(video)
        start=0
        end=tempoVideo
        num=1
        while (start < duration):
                nomeVideo=outputPrefix+str(num)+getExt(video)
                params = '-ss {start} -t {end} -i "{input}" -c copy -y "{output}" '.format(input=video, start=start, end=tempoVideo, output=nomeVideo)
                execFfmpeg(params) 
                start=end
                end=start+tempoVideo
                num+=1
	
        return

def splitVideoKeyFrames(video, outputPrefix='out'):
        execFfmpeg('-i "{input}" -acodec copy -f segment -vcodec copy -reset_timestamps 1 -map 0 -y "{prefix}%d{ext}"'.format(input=video, prefix=outputPrefix,ext=getExt(video)))

def concatFilesDirect(files, output):
        inputVideos= ''

        for f in files:
                inputVideos = inputVideos+' -i "'+f+'"'
                
        params=inputVideos+' -filter_complex "concat=n={len}:v=1:a=0 [v]" -map "[v]" -y "{output}"'.format(len=len(files), output=output)
        execFfmpeg(params)

def concatFiles(files, output, copy=True):
        listName='tmp'+getFileName(output, False)+'.txt'
        if isfile(listName):
            os.remove(listName)

        thefile = open(listName, 'w+')
            
        for item in files:
            thefile.write("file '%s'\n" % item)

        thefile.close()

        params='-f concat -safe 0 -i "{inputList}" {copy} -y "{output}"'.format(inputList=listName, copy='-c copy' if copy else '', output=output)
        execFfmpeg(params)
        
        if isfile(listName):
            os.remove(listName)

def moveToFolder(source, Folder='output'):
    if (Folder == ""):
        return source

    if not os.path.exists(Folder):
        os.makedirs(Folder)

    newVideo=Folder+"\\"+getFileName(source)
    if isfile(newVideo):
         os.remove(newVideo)
         
    os.rename(source, newVideo)
    return newVideo

def getTempFolder(file):
        folder=getFilePath(file)+os.path.splitext(getFileName(file))[0]+'tmp\\'
        if not os.path.exists(folder):
                os.makedirs(folder)

        return folder

def addPrefix(file, prefix):
          return getFilePath(file)+prefix+getFileName(file)

def reverseLongVideo(video, output):
        folder=getTempFolder(video)
        listVideos=[]
        num=splitVideoKeyFrames(video, folder+'out')
        files = [f for f in listdir(folder) if (isfile(join(folder, f)) and (os.path.splitext(f)[1].lower() in [getExt(video)]))]
        sort_nicely(files, reverse=True)
        for f in files:
                file=folder+f
                fileRev=addPrefix(file, 'rev_')
                reverse(file, fileRev)                
                listVideos.append(fileRev)

        concatFiles(listVideos, output)

        shutil.rmtree(folder)

        return output
	    

		

