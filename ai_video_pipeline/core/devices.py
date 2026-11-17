"""Opt into the verified GPU image for compatible new Blender jobs only."""
import json
import os
from pathlib import Path
import subprocess

GPU_IMAGE='ai-video-sandbox-blender-gpu:4.5.16'


def blender_gpu_profile(workspace:Path,preference='cpu'):
    preference=str(os.environ.get('FACELESS_GPU',preference)).lower()
    if preference in ('cpu','0','false','off'):return None
    if preference not in ('auto','gpu','1','true','on'):raise ValueError('blender_device must be cpu, auto or gpu')
    state=workspace/'.cache'/'blender_gpu.json'
    reason='No verified Blender GPU profile'
    if state.exists():
        try:
            profile=json.loads(state.read_text())
            if not isinstance(profile,dict):raise ValueError('Invalid GPU profile')
            if profile.get('verified') is True and profile.get('backend') in ('CUDA','OPTIX') and profile.get('image')==GPU_IMAGE:
                result=subprocess.run(['docker','image','inspect','--format','{{.Id}}',GPU_IMAGE],capture_output=True,text=True,timeout=10)
                if result.returncode==0 and result.stdout.strip()==profile.get('image_id'):
                    runtime=subprocess.run(['docker','info','--format','{{json .Runtimes}}'],capture_output=True,text=True,timeout=10)
                    if runtime.returncode==0 and 'nvidia' in json.loads(runtime.stdout):
                        return dict(profile,required=preference!='auto')
                    reason='Docker NVIDIA runtime is not configured'
                else:reason='GPU image differs from its verified profile'
        except (ValueError,TypeError,OSError,subprocess.SubprocessError):reason='GPU profile could not be verified'
    if preference!='auto':raise RuntimeError(reason+'; run GPU verification before requiring GPU')
    return None
