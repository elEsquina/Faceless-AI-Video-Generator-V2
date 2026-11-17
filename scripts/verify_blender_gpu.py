#!/usr/bin/env python3
"""Replay a job's GPU render probe and register only its successful image ID.

Usage: python scripts/verify_blender_gpu.py e42f8010
Evidence and executable scene stay inside that job's qa/gpu_oidn directory.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('job_id',help='Job containing qa/gpu_oidn/render.py and its staged helpers')
    args=parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',args.job_id):parser.error('Invalid job ID')
    root=Path(__file__).resolve().parents[1]
    sandbox=root/'video_docker_sandbox';workspace=sandbox/'workspace'
    probe=workspace/'jobs'/args.job_id/'qa/gpu_oidn'
    if not (probe/'render.py').is_file():parser.error('This job has no GPU render probe')
    image='ai-video-sandbox-blender-gpu:4.5.16'
    image_id=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',image],text=True).strip()
    result_file=probe/'result.json'
    result_file.unlink(missing_ok=True)  # stale proof must never register an image
    command=['docker','compose','-f','compose.yaml','-f','compose.gpu.yaml','run','--rm','--no-deps',
             '--env','FACELESS_GPU_REQUIRED=1','blender','blender','-b','--python',
             f'/workspace/jobs/{args.job_id}/qa/gpu_oidn/render.py']
    with (probe/'verification.log').open('w') as log:
        subprocess.run(command,cwd=sandbox,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
    result=json.loads(result_file.read_text())
    if not (result.get('verified') is True and result.get('device')=='GPU' and
            result.get('backend') in ('CUDA','OPTIX') and result.get('devices') and
            len(result.get('frame_seconds',[]))>=3):
        raise RuntimeError('GPU render did not produce valid proof')
    after=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',image],text=True).strip()
    if after!=image_id:raise RuntimeError('Image changed during verification')
    profile=dict(result,image=image,image_id=image_id,verification=str(result_file.relative_to(workspace)))
    cache=workspace/'.cache/blender_gpu.json';cache.parent.mkdir(exist_ok=True)
    temporary=cache.with_suffix('.tmp');temporary.write_text(json.dumps(profile,indent=2));temporary.replace(cache)
    print(json.dumps(profile,indent=2))


if __name__=='__main__':main()
