"""Behavioral regression checks for production staging, math and acceptance gates."""
import importlib.util
import json
from pathlib import Path
import pytest
from ai_video_pipeline.core.production import stage_production
from ai_video_pipeline.quality.geometry import check_layout
from ai_video_pipeline.quality.evidence import acceptance, fingerprint
from ai_video_pipeline.quality.validator import QualityValidator
from ai_video_pipeline.schemas.job_schemas import JobQAReportModel, VisualReviewModel


def test_stages_executable_helpers_for_every_channel(tmp_path):
    for channel in ('kids_animated_story','general_explanatory','cs_math_educational'):
        job=tmp_path/channel
        manifest=stage_production(job,channel)
        assert manifest['files']
        assert all((job/'scenes'/'_production'/name).is_file() for name in manifest['files'])


def test_layout_detects_real_collisions_and_caption_obstruction():
    items=[{'id':'formula','kind':'equation','bounds':[.2,.2,.7,.4],'collision_group':'labels'},
           {'id':'label','kind':'text','bounds':[.6,.3,.8,.5],'collision_group':'labels'},
           {'id':'point','bounds':[.4,.8,.5,.9]}]
    issues=check_layout([{'time':1,'objects':items}])
    assert any('collision' in i for i in issues)
    assert any('caption' in i for i in issues)
    # Deliberate containment is allowed unless declared collision peers.
    items[1].pop('collision_group');items.pop()
    assert not check_layout([{'objects':items}])


def test_no_approval_without_actual_evidence(tmp_path):
    with pytest.raises(ValueError,match='inspect_video'):
        QualityValidator().save_visual_review(tmp_path,{'job_id':'1234abcd','overall_status':'approved'})


def test_changed_scene_invalidates_approval(tmp_path):
    (tmp_path/'scenes').mkdir();code=tmp_path/'scenes'/'scene.py';code.write_text('original')
    review=VisualReviewModel(job_id='1234abcd',overall_status='approved',artifact_fingerprint=fingerprint(tmp_path))
    report=JobQAReportModel(job_id='1234abcd',overall_status='passed',ai_review=review)
    assert acceptance(tmp_path,report)=='approved'
    code.write_text('repaired')
    assert acceptance(tmp_path,report)=='stale_review'


def test_deterministic_action_sampling():
    file=Path('.agents/skills/video-kids/scripts/motion.py')
    spec=importlib.util.spec_from_file_location('motion',file);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for action in module.ACTIONS:
        pose=module.sample(action,.4)
        module.sample(action,3)
        assert module.sample(action,.4)==pose
    assert module.sample('walk',.4)['leg.L'] == -module.sample('walk',.4)['leg.R']


def test_continuity_and_interaction_constraints():
    from ai_video_pipeline.quality.geometry import check_continuity
    issues=check_continuity([
        {'style':'storybook','characters':[{'id':'Pip','appearance_hash':'one','expression':'sad'}]},
        {'style':'neon','characters':[{'id':'Pip','appearance_hash':'two'}],
         'interactions':[{'id':'handoff','hand':[0,0,0],'target':[1,0,0]}],
         'camera_jump':True}])
    assert any('identity' in i for i in issues)
    assert any('expression' in i for i in issues)
    assert any('contact' in i for i in issues)
    assert any('style' in i for i in issues)
    assert any('abrupt' in i for i in issues)


def test_scene_cache_keeps_unmodified_scene_but_invalidates_helpers(tmp_path):
    from types import SimpleNamespace
    from ai_video_pipeline.core.production import scene_signature
    from ai_video_pipeline.schemas.models import AnimationEngine
    scenes=tmp_path/'scenes';scenes.mkdir();(scenes/'one.py').write_text('one');(scenes/'two.py').write_text('two')
    (tmp_path/'plan.json').write_text(json.dumps({'scenes':[{'scene_id':'scene_001','code_file':'one.py'},{'scene_id':'scene_002','code_file':'two.py'}]}))
    scene=SimpleNamespace(scene_id='scene_001',engine=AnimationEngine.MANIM,start_time=0,end_time=5,code_file='one.py')
    before=scene_signature(tmp_path,scene)
    (scenes/'two.py').write_text('repair two')
    assert scene_signature(tmp_path,scene)==before
    (scenes/'_production').mkdir();(scenes/'_production'/'helper.py').write_text('new utility')
    assert scene_signature(tmp_path,scene)!=before


def test_empty_geometry_cannot_claim_a_pass():
    with pytest.raises(ValueError,match='nonempty'):
        check_layout([])


def test_approval_rejects_uninspected_and_substantive_defects(tmp_path):
    from ai_video_pipeline.schemas.job_schemas import SceneQAMetricsModel
    qa=tmp_path/'qa';qa.mkdir();frame=qa/'frame.jpg';frame.write_bytes(b'evidence')
    report=JobQAReportModel(job_id='1234abcd',overall_status='passed',total_scenes=1,scenes_passed=1,
        scene_reports={'scene_001':SceneQAMetricsModel(scene_id='scene_001',evidence_frames={'middle':str(frame)})},
        final_evidence_frames={'middle':str(frame)})
    (qa/'quality_report.json').write_text(report.model_dump_json())
    base={'job_id':'1234abcd','overall_status':'approved','artifact_fingerprint':fingerprint(tmp_path)}
    with pytest.raises(ValueError,match='identify all'):
        QualityValidator().save_visual_review(tmp_path,base)
    base['inspected_frames']=[str(frame)]
    base['issues']=[{'scene_id':'scene_001','severity':'high','issue_type':'collision','description':'Equation overlaps label'}]
    with pytest.raises(ValueError,match='substantive'):
        QualityValidator().save_visual_review(tmp_path,base)


def test_narration_windows_preserve_shot_times_and_gaps():
    from types import SimpleNamespace as S
    from ai_video_pipeline.core.timeline import narration_windows
    plan=S(scenes=[S(scene_id='scene_001',start_time=0,end_time=30,narration_text='fallback')])
    first=S(scene_id='scene_001',start_time=6,end_time=10,text='lost',voice_id=None)
    second=S(scene_id='scene_001',start_time=20,end_time=25,text='family',voice_id=None)
    audio=S(narration_segments=[second,first])
    windows=narration_windows(plan,audio)
    assert [(w['start'],w['end'],w['text']) for w in windows]==[(0,6,''),(6,10,'lost'),(10,20,''),(20,25,'family'),(25,30,'')]
    second.start_time=9
    with pytest.raises(ValueError,match='Overlapping'):
        narration_windows(plan,audio)


def test_postproduction_uses_every_authored_window_and_caption_offset(tmp_path):
    from unittest.mock import patch
    from ai_video_pipeline.mcp.tools import PipelineMCPTools
    from ai_video_pipeline.schemas.models import WordTimestamp
    tools=PipelineMCPTools(workspace_root=tmp_path)
    created=tools.create_job('cs_math','Window integration',6)
    job=Path(created['job_dir']);job_id=created['job_id']
    plan={'job_id':job_id,'title':'Windows','category':'cs_math','aspect_ratio':'16:9','target_duration_seconds':6,
          'scenes':[{'scene_id':'scene_001','index':0,'engine':'manim','start_time':0,'end_time':6,
                     'narration_text':'fallback must not replace two beats','visual_description':'diagram','code_file':'scene.py'}]}
    (job/'plan.json').write_text(json.dumps(plan))
    (job/'audio_plan.json').write_text(json.dumps({'job_id':job_id,'narration_segments':[
        {'scene_id':'scene_001','text':'first beat','start_time':1,'end_time':2},
        {'scene_id':'scene_001','text':'second beat','start_time':4,'end_time':5}]}))
    (job/'renders/scene_001.mp4').write_bytes(b'mocked video')
    final=job/'output/final.mp4';final.touch()
    def generate(**kwargs):
        return kwargs['output_file'],[WordTimestamp(word=kwargs['script_text'],start_time=0,end_time=.4)],{'duration':.4}
    with patch.object(tools.tts_service,'generate_narration',side_effect=generate) as tts, \
         patch.object(tools.compositor,'assemble_narration_track',return_value=job/'audio/full.wav') as assemble, \
         patch.object(tools.compositor,'mix_audio_tracks'), \
         patch.object(tools.compositor,'concatenate_video_scenes'), \
         patch.object(tools.compositor,'assemble_final_video'), \
         patch.object(tools.compositor,'probe_media',return_value={'format':{'duration':'6'},'streams':[{'codec_type':'video'},{'codec_type':'audio'}]}), \
         patch.object(tools.text_splash,'generate_ass_subtitles') as captions:
        result=tools.retry_postproduction(job_id)
    assert result['status']=='completed'
    assert [call.kwargs['script_text'] for call in tts.call_args_list]==['first beat','second beat']
    assert [time.start_time for time in captions.call_args.kwargs['word_timestamps']]==[1,4]
    assert [duration for _,duration in assemble.call_args.args[0]]==[1,1,2,1,1]


def test_static_exception_does_not_hide_a_frozen_moving_curve(tmp_path):
    from PIL import Image,ImageDraw
    from ai_video_pipeline.quality.analyzer import FrameQualityAnalyzer
    from ai_video_pipeline.schemas.models import SceneSpec,AnimationEngine,AspectRatio
    image=Image.new('RGB',(320,180),'#101D32');draw=ImageDraw.Draw(image)
    draw.rectangle((30,30,240,130),fill='white');file=tmp_path/'curve.jpg';image.save(file)
    scene=SceneSpec(scene_id='scene_001',index=0,engine=AnimationEngine.MANIM,start_time=0,end_time=5,narration_text='',visual_description='A point moving down a curve to its minimum')
    metadata={'format':{'duration':'5'},'streams':[{'codec_type':'video','width':1280,'height':720}]}
    result=FrameQualityAnalyzer().evaluate_scene(scene,{'start':file,'middle':file,'end':file},metadata,AspectRatio.LANDSCAPE_16_9)
    assert result.is_frozen and result.status=='failed'
    metadata['streams'][0].update(width=720,height=720)
    result=FrameQualityAnalyzer().evaluate_scene(scene,{'start':file},metadata,AspectRatio.LANDSCAPE_16_9)
    assert not result.aspect_ratio_ok and result.status=='failed'


def test_gpu_profile_requires_verified_matching_image_and_runtime(tmp_path,monkeypatch):
    from unittest.mock import patch
    from types import SimpleNamespace as S
    from ai_video_pipeline.core.devices import blender_gpu_profile,GPU_IMAGE
    monkeypatch.delenv('FACELESS_GPU',raising=False)
    assert blender_gpu_profile(tmp_path,'auto') is None
    with pytest.raises(RuntimeError,match='verified'):
        blender_gpu_profile(tmp_path,'gpu')
    cache=tmp_path/'.cache';cache.mkdir();(cache/'blender_gpu.json').write_text(json.dumps({'verified':True,'backend':'CUDA','image':GPU_IMAGE,'image_id':'sha256:tested'}))
    with patch('ai_video_pipeline.core.devices.subprocess.run',side_effect=[S(returncode=0,stdout='sha256:tested\n'),S(returncode=0,stdout='{"nvidia":{}}')]):
        assert blender_gpu_profile(tmp_path,'auto')['backend']=='CUDA'
    with patch('ai_video_pipeline.core.devices.subprocess.run',return_value=S(returncode=0,stdout='sha256:changed\n')):
        assert blender_gpu_profile(tmp_path,'auto') is None
    with patch('ai_video_pipeline.core.devices.subprocess.run') as run:
        assert blender_gpu_profile(tmp_path,'cpu') is None
        run.assert_not_called()


def test_gpu_compose_override_is_explicit_and_does_not_modify_args(tmp_path):
    from unittest.mock import patch,MagicMock
    from ai_video_pipeline.parsers.omega import DockerEngineRunner
    runner=DockerEngineRunner(sandbox_dir=tmp_path);args=['run','--rm','blender','blender','-b']
    with patch('ai_video_pipeline.parsers.omega.subprocess.run',return_value=MagicMock(returncode=0,stdout='',stderr='')) as run:
        runner.run_docker(args,gpu_profile={'backend':'CUDA','required':True})
    command=run.call_args.args[0]
    assert str(tmp_path/'compose.gpu.yaml') in command
    assert 'FACELESS_BLENDER_BACKEND=CUDA' in command and 'FACELESS_GPU_REQUIRED=1' in command
    assert args==['run','--rm','blender','blender','-b']
