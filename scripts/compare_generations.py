"""Create paired old/new composed frames and a contact sheet; no visual scores.
Usage: python scripts/compare_generations.py OLD_ID NEW_ID
"""
import json
from pathlib import Path
import sys
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ai_video_pipeline.quality.frame_extractor import KeyframeExtractor


def compare(old_id,new_id):
    root=Path(__file__).resolve().parents[1]/'video_docker_sandbox/workspace/jobs'
    old,new=root/old_id,root/new_id
    out=new/'qa'/'comparison';out.mkdir(parents=True,exist_ok=True)
    extract=KeyframeExtractor();times=[3,8,16,23,27]
    sheet=Image.new('RGB',(1280,len(times)*390),'#152033');draw=ImageDraw.Draw(sheet)
    for row,t in enumerate(times):
        for col,job in enumerate((old,new)):
            frame=out/f'{"old" if col==0 else "new"}_{t:02d}.jpg'
            extract.extract_frame(job/'output/final.mp4',t,frame)
            with Image.open(frame) as im:sheet.paste(im.resize((640,360)),(col*640,row*390+26))
            draw.text((col*640+8,row*390+7),f'{job.name} | {t}s | {"previous" if col==0 else "new"}',fill='white')
    sheet.save(out/'before_after.jpg',quality=95)
    (out/'sampling.json').write_text(json.dumps({'old':old_id,'new':new_id,'times':times,'source':'final composed MP4, matched timestamps, scaled to 640x360'},indent=2))
    print(out/'before_after.jpg')


if __name__=='__main__':compare(*sys.argv[1:3])
