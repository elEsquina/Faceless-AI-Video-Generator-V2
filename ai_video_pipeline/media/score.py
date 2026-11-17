"""Original procedural score/chime assets. No samples, downloads or music API.
Usage: python -m ai_video_pipeline.media.score JOB_ID [warm|bright|calm]
"""
from array import array
import math
from pathlib import Path
import sys
import wave
from ai_video_pipeline.jobs.manager import JobManager


def write_pcm(path,samples,rate=24000):
    pcm=array('h',(int(max(-1,min(1,s))*16000) for s in samples))
    if sys.byteorder!='little':pcm.byteswap()
    with wave.open(str(path),'wb') as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(rate);out.writeframes(pcm.tobytes())


def synthesize(job_id,style='warm',duration=30):
    if style not in ('warm','bright','calm'):raise ValueError(style)
    rate=24000;out=JobManager().get_job_dir(job_id)/'assets';out.mkdir(exist_ok=True)
    notes={'warm':[60,64,67,69,67,64,62,67,64,60,62,60],
           'bright':[60,67,64,72,69,67,64,67,72,67,64,60],
           'calm':[57,60,64,67,64,60,57,64,60,57,60,57]}[style]
    samples=array('f',[0])*int(duration*rate)
    beat=duration/len(notes)
    for index,midi in enumerate(notes):
        start=int(index*beat*rate);length=min(int(beat*1.1*rate),len(samples)-start)
        for semitone,gain in [(0,.13),(-12,.07)]:
            frequency=440*2**((midi+semitone-69)/12)
            for j in range(length):
                t=j/rate;envelope=min(1,t/.12)*math.exp(-t/1.2)*min(1,(length-j)/(rate*.2))
                samples[start+j]+=gain*envelope*(math.sin(2*math.pi*frequency*t)+.15*math.sin(4*math.pi*frequency*t))
    write_pcm(out/'score.wav',samples,rate)
    chime=[.20*math.exp(-5*i/rate)*math.sin(2*math.pi*880*i/rate)*min(1,i/(rate*.01)) for i in range(rate)]
    write_pcm(out/'chime.wav',chime,rate)
    return out


if __name__=='__main__':print(synthesize(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else 'warm'))
