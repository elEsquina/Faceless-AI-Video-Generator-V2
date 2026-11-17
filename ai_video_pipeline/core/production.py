"""Stage versioned, executable director tools into every new job (no AI service)."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHANNELS = {
    'kids_animated_story': ('video-kids', ['kids_stage.py', 'motion.py']),
    'general_explanatory': ('video-explainer', ['cinematic.tsx', 'models.tsx']),
    'cs_math_educational': ('video-cs-math', ['math_stage.py']),
}


def stage_production(job_dir: Path, category: str) -> dict:
    skill, files = CHANNELS[category]
    source = ROOT / '.agents' / 'skills' / skill
    target = job_dir / 'scenes' / '_production'
    target.mkdir(parents=True, exist_ok=True)
    (target / '__init__.py').write_text('', encoding='utf-8')
    manifest = {'skill': str(source / 'SKILL.md'), 'files': {}, 'visual_approval_required': True}
    for filename in files:
        origin = source / 'scripts' / filename
        shutil.copy2(origin, target / filename)
        manifest['files'][filename] = hashlib.sha256(origin.read_bytes()).hexdigest()
    for asset in (source / 'assets').glob('*.json'):
        shutil.copy2(asset, target / asset.name)
        manifest['files'][asset.name] = hashlib.sha256(asset.read_bytes()).hexdigest()
    (job_dir / 'production_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    if category == 'kids_animated_story' and not (job_dir / 'render_settings.json').exists():
        (job_dir / 'render_settings.json').write_text(json.dumps({'blender_device': 'auto'}, indent=2), encoding='utf-8')
    return manifest


def scene_signature(job_dir: Path, scene) -> str:
    """Rendering cache is valid only for the same source, helper versions and preset."""
    h = hashlib.sha256()
    h.update(str((scene.engine.value, scene.start_time, scene.end_time)).encode())
    paths = list((job_dir / "scenes" / "_production").rglob("*"))
    if scene.code_file:
        code = job_dir / "scenes" / scene.code_file
        if not code.exists(): code = job_dir / scene.code_file
        paths.append(code)
        # Support job-authored helpers beside the entry, excluding other scene entries.
        other_entries = set()
        for manifest_name in ("storyboard.json", "plan.json"):
            manifest_file = job_dir / manifest_name
            if manifest_file.exists():
                for spec in json.loads(manifest_file.read_text()).get("scenes", []):
                    if spec.get("scene_id") != scene.scene_id and spec.get("code_file"):
                        other_entries.add((job_dir / "scenes" / spec["code_file"]).resolve())
                        other_entries.add((job_dir / spec["code_file"]).resolve())
                break
        paths += [p for p in code.parent.rglob("*") if p.resolve() not in other_entries]
    else:
        h.update((scene.inline_code or "").encode())
    paths += [job_dir / "render_settings.json"]
    for path in sorted(set(p for p in paths if p.is_file() and "__pycache__" not in p.parts)):
        h.update(str(path.relative_to(job_dir)).encode())
        h.update(path.read_bytes())
    return h.hexdigest()
