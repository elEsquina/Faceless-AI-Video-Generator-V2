"""Hash rendered artifacts and inspected frames so edits invalidate approval."""
import hashlib
import json
from pathlib import Path


def fingerprint(job_dir: Path):
    paths=[]
    for name in ('plan.json','storyboard.json','audio_plan.json','request.json','render_settings.json','production_manifest.json','storyboard_design.json'):
        if (job_dir/name).exists(): paths.append(job_dir/name)
    for folder,pattern in [('scenes','*'),('renders','*.mp4'),('output','*.mp4'),('qa/scenes','*.jpg'),('qa/final','*.jpg')]:
        paths.extend(p for p in (job_dir/folder).rglob(pattern) if p.is_file() and '__pycache__' not in p.parts)
    paths.extend((job_dir/'qa').glob('layout*.json'))
    h=hashlib.sha256()
    for path in sorted(set(paths)):
        h.update(str(path.relative_to(job_dir)).encode())
        with path.open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def acceptance(job_dir, report):
    review=report.ai_review
    if report.scenes_failed or any(m.status!='passed' for m in report.scene_reports.values()):return 'needs_repair'
    if review is None:return 'pending_visual_review'
    if review.artifact_fingerprint!=fingerprint(job_dir):return 'stale_review'
    if review.overall_status!='approved':return review.overall_status
    if review.scenes_to_repair or any(i.severity in ('medium','high','critical') for i in review.issues):return 'needs_repair'
    return 'approved'
