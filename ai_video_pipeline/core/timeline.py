"""Explicit narration windows on the same global timeline as authored visuals."""
from pathlib import Path
import wave


def narration_windows(plan,audio_plan):
    windows=[]
    known={scene.scene_id for scene in plan.scenes}
    if any(seg.scene_id not in known for seg in audio_plan.narration_segments):
        raise ValueError('Narration references an unknown scene')
    for scene in plan.scenes:
        segments=sorted((s for s in audio_plan.narration_segments if s.scene_id==scene.scene_id),key=lambda s:s.start_time)
        if not segments:
            windows.append(dict(scene_id=scene.scene_id,start=scene.start_time,end=scene.end_time,text=scene.narration_text,voice_id=None))
            continue
        cursor=scene.start_time
        for seg in segments:
            if seg.start_time<cursor-1e-6 or seg.end_time>scene.end_time+1e-6 or seg.end_time<=seg.start_time:
                raise ValueError(f'Overlapping or out-of-scene narration interval in {scene.scene_id}')
            if seg.start_time>cursor+1e-6:
                windows.append(dict(scene_id=scene.scene_id,start=cursor,end=seg.start_time,text='',voice_id=None))
            windows.append(dict(scene_id=scene.scene_id,start=seg.start_time,end=seg.end_time,text=seg.text,voice_id=seg.voice_id))
            cursor=seg.end_time
        if cursor<scene.end_time-1e-6:
            windows.append(dict(scene_id=scene.scene_id,start=cursor,end=scene.end_time,text='',voice_id=None))
    return windows


def silence(path:Path,duration:float,rate=24000):
    path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),'wb') as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(rate)
        count=int(round(duration*rate))
        while count:
            chunk=min(count,rate);out.writeframes(b'\0\0'*chunk);count-=chunk
    return path
