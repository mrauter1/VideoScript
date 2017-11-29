from subprocess import Popen
import os 
from os import rename, listdir
from os.path import isfile, join

def getFfmpeg():
#	return '"'+dir_path+'\\..\\ffmpeg.exe" '
	return '"C:\\Users\\Marcelo\\Desktop\\youtube\\ffmpeg.exe" '
	
def doFadeInFadeOut(video):
  if (video.startswith("fifo_")):
	  return video
	  
  newVid = 'fifo_'+video   
  params = '-i {0} -sseof -1 -copyts -i {0} -filter_complex "[1]fade=out:0:10[t];[0][t]overlay,fade=in:0:30[v]" '.format(video)  
  params=params+'-map "[v]" -c:v libx264 -crf 22 -preset veryfast -shortest {1}'.format(video, newVid)  
# fade with audio  
#  params = '-i {0} -sseof -1 -copyts -i {0} -filter_complex "[1]fade=out:0:10[t];[0][t]overlay,fade=in:0:30[v]; anullsrc,atrim=0:2[at];'.format(video)
#  params=params+'[0][at]acrossfade=d=1,afade=d=1[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 22 -preset veryfast -shortest {1}'.format(video, newVid)
  print(getFfmpeg()+params)
  p = Popen(getFfmpeg()+params, shell=True)
  stdout, stderr = p.communicate()	
  rename(video, video+'.bkp')
  return newVid	  
  
def addAudioFade(video):
  newVideo='a_'+video
  
  params='-i {0} -sseof -1 -copyts -i {0} -filter_complex "anullsrc,atrim=0:3[at];[0][at]acrossfade=d=2,afade=d=2[a]" '.format(video)
  params=params+'-map 0:v -map "[a]" -c:v libx264 -crf 22 -preset veryfast -shortest {0}'.format(newVideo)
  p = Popen(getFfmpeg()+params, shell=True)
  stdout, stderr = p.communicate()	
  print(getFfmpeg()+params)
  
  if os.path.isfile(newVideo): 
    os.remove(video)
    rename(newVideo, video)    
  
def getLabel(cnt):
	return 'L{0}'.format(cnt)
	  
def addAudio(video):
  audios = [a for a in listdir(dir_path) if (isfile(join(dir_path, a)) and (os.path.splitext(a)[1].lower() in ['.mp3']))]

  audios.sort()
  
  if audios.count==0:
    return
  
  newVideo='v_'+video
  
  count=0
  inputAudio=''
  param2=''
  param3=''
  #Seleciona o primeiro mp3 da pasta
  for a in audios:
    if a=="audio.mp3":
      continue	
  
    inputAudio=inputAudio+' -i "'+a+'"'
    param2=param2+'[{0}:a]'.format(count+1)
    param3=param3+'[{0}:0]'.format(count)
    count+=1

  paramConcat = inputAudio+' -filter_complex "'+param3+' concat=n='+str(count)+':v=0:a=1 [out]" -map "[out]" -y "audio.mp3"'	
  p = Popen(getFfmpeg()+paramConcat, shell=True)
  stdout, stderr = p.communicate()	
  print(getFfmpeg()+paramConcat)

#  params = '-i {0} {1} -filter_complex "{2}amerge=inputs={3}[a]" -map 0:v -map "[a]" -c:v copy -c:a libvorbis -ac 2 -shortest "{4}"'.format(oldVideo, inputAudio, param2, count, video)
  params = '-i {0} -i audio.mp3 -filter_complex "[1:0]amerge=inputs=1[a]" -map 0:v -map "[a]" -c:v copy -c:a libvorbis -ac 2 -shortest "{1}"'.format(video, newVideo)

  p = Popen(getFfmpeg()+params, shell=True)
  stdout, stderr = p.communicate()	
  print(getFfmpeg()+params)
  
  if os.path.isfile(newVideo): 
    os.remove(video)
    rename(newVideo, video)    
  
  addAudioFade(video)
  
	
dir_path = os.path.dirname(os.path.realpath(__file__))

files = [f for f in listdir(dir_path) if (isfile(join(dir_path, f)) and (os.path.splitext(f)[1].lower() in ['.mkv', '.mp4']))]

files.sort()

cnt=0

inputVideos = ''
count=0
param=' '
param2=''
param3=' '
param4=' '
totFiles=len(files)

for f in files:
  cnt+=1

  if (f=='output.mkv'):
    continue	
	
  print(f)
  
#  newVid=''
#  newVid=doFadeInFadeOut(f)
 
  inputVideos = inputVideos+' -i "'+f+'"'
  
  param2=param2+'[{0}]scale=1280x720,setdar=16/9[{1}];'.format(count, getLabel(count))
  param3=param3+'['+getLabel(count)+']'
  param=param+'[{0}][{1}:a] '.format(getLabel(count), count)  

  count=count+1
  
print(inputVideos)

file = getFfmpeg()+ inputVideos +' -filter_complex "'+param2+' '+param3+' concat=n='+str(count)+':v=1:a=0 [v]" -map "[v]"  "output.mkv"'

p = Popen(file, shell=True)

stdout, stderr = p.communicate()

addAudio("output.mkv")

print(file)
print("Done")