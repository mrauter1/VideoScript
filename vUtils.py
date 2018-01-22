from os import rename, listdir
import os 
from os.path import isfile, join
import re
import shutil
from subprocess import Popen,PIPE,STDOUT
import sys

#defaultOutOptions='-r 60 -c:v libx264 -b:v 2.8M -c:a aac -b:a 192k -ac 2 -profile:v baseline -video_track_timescale 60000 -preset medium -ar 48000 -y'
defaultOutOptions='-r 60 -c:v libx264 -c:a aac -b:a 192k -ac 2  -crf 17 -profile:v baseline -video_track_timescale 60000 -preset medium -ar 48000 -y'

def sameFile(file1, file2):
    if ((os.path.abspath(os.path.realpath(file1.upper()))) == (os.path.abspath(os.path.realpath(file2.upper())))):
        return True
    else:
        return False    
    
class Media:

    def __init__(self, mediaPath, inputNo):
        self.mediaPath=mediaPath
        self.vFilters=[]
        self.audioFilters=[]
        self.hasAudio=True
        self.hasVideo=True

        self.vLabel='['+str(inputNo)+':v]'
        self.aLabel='['+str(inputNo)+':a]'        

    def addFilter(self, filter_):
        self.vFilters.append(filter_)
        self.vLabel=filter_.Label

    def addAudioFilter(self, filter_):
        self.audioFilters.append(filter_)
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
        self.vMap=''
        self.aMap=''
        self.inOptions=' '
        #self.outOptions='-c:v libx264 -c:a aac -crf 23 -preset medium -vf -ac 2 -b:a 192k -f format=yuv420p '
        self.outOptions=defaultOutOptions 
        
    def lastVideoLabel(self):
        if self.lastVideoLabelNum > 0:
            return '[v{0}]'.format(str(self.lastVideoLabelNum))
        else:
            return '0:v'            
        
    def lastAudioLabel(self):
        if self.lastAudioLabelNum > 0:
            return '[a{0}]'.format(str(self.lastAudioLabelNum))
        else:
            return '0:a'             
        
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
        
    def normalizeInputs(self, videoFilter, audioFilter):
        for m in self.inputs:
            if videoFilter:
                self.vFilterMedia(m, videoFilter)
            if audioFilter:	
                self.audioFilterMedia(m, audioFilter)			
		
    def vFilter(self, origin, filterStr):
        block = Block(None)
        block.origin = origin
        block.Label = self.nextVideoLabel()
        block.Filter = filterStr
        self.blocks.append(block)
        return block
    
    def audioFilter(self, origin, filterStr):
        block = Block(None)
        block.origin=origin
        block.Label = self.nextAudioLabel()
        block.Filter = filterStr
        self.blocks.append(block)
        return block
    
    def vFilterMedia(self, media, filterStr):
        f = self.vFilter(media.vLabel, filterStr)
        media.addFilter(f)
        
    def audioFilterMedia(self, media, filterStr):
        f = self.audioFilter(media.aLabel, filterStr)
        media.addAudioFilter(f)    
        
    def trimMedia(self, media, start, end):
        self.vFilterMedia(media, )
        self.audioFilterMedia(media, )
    
    def concat(self, inLabels, v=1, a=1):
        vLabel=''
        if v>0:
            vLabel=self.nextVideoLabel()
        aLabel=''
        if a>0:
            aLabel=self.nextAudioLabel()            
        
        block = ConcatBlock(inLabels, v, a,  vLabel, aLabel)
        self.blocks.append(block)
        return block
    
    def changePts(self, vLabel, aLabel, pts):
        atempo=round(1.0/pts,3)            
        vBlock = self.vFilter(vLabel, 'setpts='+str(pts)+'*PTS')
        aBlock = self.audioFilter(aLabel, 'atempo='+str("%.3f" % atempo))
        return vBlock, aBlock
    
    def getvMap(self):
        return self.vMap if self.vMap else self.lastVideoLabel()
    
    def getaMap(self):
        return self.aMap if self.aMap else self.lastAudioLabel()
   
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
            
        if filters:
            filters='-filter_complex "'+filters+'"'                              

        return inputs +' '+self.inOptions+' '+filters+' -map "'+self.getvMap()+'" -map "'+self.getaMap()+'" '+self.outOptions+' "'+output+'"'
        
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
                b=Block()
                b.Filte = filter
                m.addVFilter(b)
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
            if (len(m.audioFilters) == 0):
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
                    videoFilters = videoFilters+'[{0}:v]{1}[v{0}];'.format(cnt, v.Filter)

            for a in m.audioFilters:
                audioFilters = audioFilters+'[{0}:a]{1}[a{0}];'.format(cnt, a.Filter)

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
    if printCmd:
        print(cmd)
         
    p = Popen(cmd, shell=True)
    stdout, stderr = p.communicate() 
	
def getFfprobe():
	return '"'+getCurDir()+'\\..\\ffprobe.exe" '	
	
def shellExecOutput(cmd):
        import subprocess
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        return process.communicate()[0].decode("utf-8")

def getFfmpeg():
	return '"'+getCurDir()+'\\..\\ffmpeg.exe" '
#return "ffmpeg.exe "
	
def execFFprobe(params):
	shellExec(getFfprobe()+params)
	
def execFfmpeg(params):
	shellExec(getFfmpeg()+params)

def execYoutubedl(params):
    retorno = shellExecOutput('"'+getCurDir()+'\\..\\youtube-dl.exe" '+params)

    return retorno.strip()    

def getDuration(video):
	retorno = shellExecOutput(getFfprobe()+' -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{0}"'.format(video))
	return float(retorno.strip())

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

	
outParams='-c:v libx264 -c:a aac -b:a 192k -crf 23 23 '

def doFadeInFadeOut(video):
  if ("fifo_" in video):
	  return video
	  
  newVid = 'fifo_'+video   
  params = '-i {0} -sseof -1 -copyts -i {0} -filter_complex "[1]fade=out:0:10[t];[0][t]overlay,fade=in:0:30[v]" '.format(video)  
  params=params+'-map "[v]" -c:v libx264 -crf 23 22 -preset veryfast -shortest {1}'.format(video, newVid)  
# fade with audio  
#  params = '-i {0} -sseof -1 -copyts -i {0} -filter_complex "[1]fade=out:0:10[t];[0][t]overlay,fade=in:0:30[v]; anullsrc,atrim=0:2[at];'.format(video)
#  params=params+'[0][at]acrossfade=d=1,afade=d=1[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 23 22 -preset veryfast -shortest {1}'.format(video, newVid)
  execFfmpeg(params)
  
  rename(video, video+'.bkp')
  return newVid

def changePts(file, pts, output):
    atempo=round(1.0/pts,3)    
    #params = '-i "{input}" -r 60 -filter:v  "setpts={pts}*PTS" -y "{output}" '.format(input=file, pts=pts, output=newFile)
    
    params=('-i "{input}" -r 60 -filter_complex "[0:v]setpts={pts}*PTS[av];[av]scale=1600:900,setdar=16/9[v];[0:a]atempo={atempo}[a]" -map "[v]" -map "[a]" {outParams} -y "{output}"'.
            format(input=file, pts=pts, atempo=atempo, outParams=outParams, output=output))
    execFfmpeg(params)
    
def convertCodec(file, output):
        params = '-i "{0}" -vf "scale=1600:900,setdar=16/9" {1} "{2}" '.format(file, outParams, output)  
  
        execFfmpeg(params)       
		
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
        
def addPrefix(file, prefix):
          return getFilePath(file)+prefix+getFileName(file)        
        
def reencode(file, newOutput='', videoProcessing='', audioProcessing=''):
        if newOutput:
            newFile=newOutput
        else:
            newFile=addPrefix(file, 'tmp')
            
        f=Filters()
         
        video=f.newMediaInput(file) 
        f.vFilterMedia(video, 'scale=1600x900,settb=AVTB')    
        
        if videoProcessing:    
            f.vFilterMedia(video, videoProcessing)

        if audioProcessing:             
            f.audioFilterMedia(video, audioProcessing)
        else:
            f.aMap='0:a'        

        f.outOptions = defaultOutOptions        

        execFfmpeg(f.getCmdLine(newFile))
        
        if (newOutput=='') and (isfile(newFile)):
           os.remove(file)                      
           os.rename(newFile, file)                    

def concatFiles(files, output, copy=True, Reencode=False):
        if (Reencode):
            for n,f in enumerate(files):
                newf=addPrefix(f, 'tmp')
                #reencode(f, newf)
                files[n]=newf
                    
        listName='tmp'+getFileName(output, False)+'.txt'
        if isfile(listName):
            os.remove(listName)

        thefile = open(listName, 'w+')
            
        for item in files:
            thefile.write("file '%s'\n" % item)

        thefile.close()
# -video_track_timescale 18000 
        params='-f concat -safe 0 -i "{inputList}" {copy} -y "{output}"'.format(inputList=listName, copy='-c copy' if copy else '', output=output)
        print(params)
        execFfmpeg(params)
        
    #    if isfile(listName):
    #        os.remove(listName)

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
    
def reverse(file, output, outParams='', removeOriginal=True):   
        params = '-i "{0}" -vf "reverse" -af areverse {1} "{2}" '.format(file, outParams, output)  
  
        print(params)
        execFfmpeg(params) 
  
        if (os.path.isfile(output)) & (removeOriginal): 
            os.remove(file)         

def reverseLongVideo(video, output, outParams=''):
        folder=getTempFolder(video)
        listVideos=[]
        num=splitVideoKeyFrames(video, folder+'out')
        files = [f for f in listdir(folder) if (isfile(join(folder, f)) and (os.path.splitext(f)[1].lower() in [getExt(video)]))]
        sort_nicely(files, reverse=True)
        for f in files:
                file=folder+f
                fileRev=addPrefix(file, 'rev_')
                reverse(file, fileRev, outParams)                
                listVideos.append(fileRev)

        concatFiles(listVideos, output)

        shutil.rmtree(folder)

        return output



