"""Sequential low-resolution previews using the same installed engine adapters.
Usage: python scripts/preview_scene.py JOB_ID --frames 90 240 450 690 810
Final execution remains an explicit MCP execute_job call after image inspection.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ai_video_pipeline.core.director import ExternalDirectorBridge
from ai_video_pipeline.core.devices import blender_gpu_profile
from ai_video_pipeline.jobs.manager import JobManager
from ai_video_pipeline.parsers.omega import ParserOmega
from ai_video_pipeline.quality.frame_extractor import KeyframeExtractor


def preview(job_id,frames,scene_id=None):
    job=JobManager().get_job_dir(job_id);plan=ExternalDirectorBridge().load_plan_manifest(job)
    scene=next(s for s in plan.scenes if scene_id is None or s.scene_id==scene_id)
    parser=ParserOmega();code=parser.ingest_scene_animation(job,scene)
    valid,error=parser.validate_scene_code(scene,code)
    if not valid:raise ValueError(error)
    qa=job/'qa';qa.mkdir(exist_ok=True);os.chmod(qa,0o777)
    out=qa/'preview';out.mkdir(exist_ok=True);os.chmod(out,0o777)
    rel=code.resolve().relative_to(parser.runner.workspace_dir.resolve())
    logfile=job/'logs'/'preview.log';events={}
    if scene.engine.value=='three_js_remotion':
        parser.stage_remotion_scene(job,code)
        driver=qa/'preview_driver.cjs'
        shutil.copy2(Path(__file__).with_name('preview_remotion.cjs'),driver)
        reljob=job.relative_to(parser.runner.workspace_dir)
        result=parser.runner.run_docker(['run','--rm','remotion','node',f'/workspace/{reljob}/qa/preview_driver.cjs',
            f'/workspace/{reljob}',','.join(map(str,frames))],log_file=logfile,timeout=300)
        if result.returncode:raise RuntimeError(f'Preview failed; inspect {logfile}')
        layout=qa/f'layout_{scene.scene_id}.json'
        if layout.exists():events={i:s for i,s in enumerate(json.loads(layout.read_text())['samples'])}
    elif scene.engine.value=='blender':
        settings=json.loads((job/'render_settings.json').read_text()) if (job/'render_settings.json').exists() else {}
        profile=blender_gpu_profile(parser.runner.workspace_dir,settings.get('blender_device','cpu'))
        options={'gpu_profile':profile} if profile is not None else {}
        result=parser.runner.run_docker(['run','--rm','blender','blender','-b','-t','8','-P',f'/workspace/{rel}',
            '--','--still-frames='+','.join(map(str,frames))],log_file=logfile,timeout=300,**options)
        if result.returncode:raise RuntimeError(f'Preview failed; inspect {logfile}')
    elif scene.engine.value=='manim':
        cls=parser.manim_handler.find_scene_class(code)
        relout=out.relative_to(parser.runner.workspace_dir)
        result=parser.runner.run_docker(['run','--rm','manim','-ql','--disable_caching','--media_dir',f'/manim/{relout}',str(rel),cls],log_file=logfile,timeout=300)
        if result.returncode:raise RuntimeError(f'Preview failed; inspect {logfile}')
        candidates=[p for p in out.rglob('*.mp4') if 'partial_movie_files' not in p.parts]
        video=max(candidates,key=lambda p:p.stat().st_mtime)
        KeyframeExtractor().extract_scene_keyframes(video,scene.end_time-scene.start_time,out/'frames',additional_timestamps=[f/30 for f in frames])
    else:
        raise ValueError(f'Unsupported preview engine: {scene.engine}')
    print(json.dumps({'job_id':job_id,'preview_dir':str(out),'log':str(logfile),'geometry_samples':len(events)}))


if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('job_id');cli.add_argument('--scene');cli.add_argument('--frames',type=int,nargs='+',default=[90,240,450,690,810])
    args=cli.parse_args();preview(args.job_id,args.frames,args.scene)
