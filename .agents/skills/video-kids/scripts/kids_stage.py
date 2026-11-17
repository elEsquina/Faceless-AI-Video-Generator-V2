"""Original Blender articulated storybook cast, environment, shots and frame posing.
Meshes are authored profiles, bound to an actual armature with rigid vertex groups.
No downloaded assets. This is a stylized rigid rig, not a deformable film character.
"""
import math
import random
import bpy
from mathutils import Vector
from .motion import sample


def material(name,color,roughness=.58):
    m=bpy.data.materials.get(name)
    if m: return m
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    node=m.node_tree.nodes.get('Principled BSDF');node.inputs['Base Color'].default_value=(*color,1)
    node.inputs['Roughness'].default_value=roughness
    return m


def profile(name,rings,scale,at,mat,segments=24):
    """Closed hand-profiled surface; rings=(height,radius), arbitrary stylized contours."""
    verts=[]
    for z,r in rings:
        for i in range(segments):
            a=i*2*math.pi/segments
            verts.append((at[0]+math.cos(a)*r*scale[0],at[1]+math.sin(a)*r*scale[1],at[2]+z*scale[2]))
    faces=[]
    for j in range(len(rings)-1):
        for i in range(segments):
            k=j*segments+i;n=j*segments+(i+1)%segments
            faces.append((k,n,n+segments,k+segments))
    faces.extend([tuple(reversed(range(segments))),tuple((len(rings)-1)*segments+i for i in range(segments))])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(mat)
    for face in mesh.polygons: face.use_smooth=True
    return obj

ROUND=[(-1,.02),(-.9,.43),(-.6,.79),(-.15,1),( .35,.91),(.7,.67),(.93,.3),(1,.02)]
PEAR=[(-1,.04),(-.85,.65),(-.5,1),(0,.93),(.5,.64),(.85,.4),(1,.03)]
LEAF=[(0,.01),(.15,.55),(.45,.85),(.8,.57),(1,.01)]


def curve(name,points,radius,mat):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=radius;c.bevel_resolution=2
    sp=c.splines.new('POLY');sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):p.co=(*co,1)
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(mat)
    return o


class Character:
    def __init__(self,name,kind='rabbit',color=None,scale=1):
        if kind not in ('rabbit','turtle'):raise ValueError(kind)
        self.name,self.kind=name,kind
        skin=material(name+'_skin',color or ((.69,.49,.32) if kind=='rabbit' else (.34,.61,.31)))
        cream=material('cream',(.95,.83,.63));dark=material('ink',(.025,.038,.054),.28)
        pink=material('rose',(.87,.38,.35));white=material('eye_white',(.97,.98,1),.23)
        vest=material(name+'_vest',(.10,.35,.40));shell=material(name+'_shell',(.22,.35,.13))
        # Rest coordinates use z up and -y forward. Bones are real armature bones.
        data=bpy.data.armatures.new(name+'_skeleton');self.root=bpy.data.objects.new(name,data)
        bpy.context.collection.objects.link(self.root);bpy.context.view_layer.objects.active=self.root
        self.root.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
        specs={'body':((0,0,.5),(0,0,1.2),None),'head':((0,0,1.35),(0,0,1.95),'body'),
          'arm.L':((-.42,0,1.25),(-.48,0,.66),'body'),'arm.R':((.42,0,1.25),(.48,0,.66),'body'),
          'leg.L':((-.25,0,.57),(-.25,0,.16),'body'),'leg.R':((.25,0,.57),(.25,0,.16),'body'),
          'ear.L':((-.23,0,2.05),(-.30,0,2.85),'head'),'ear.R':((.23,0,2.05),(.30,0,2.85),'head')}
        for key,(head,tail,parent) in specs.items():
            b=data.edit_bones.new(key);b.head=head;b.tail=tail
            if parent:b.parent=data.edit_bones[parent]
        bpy.ops.object.mode_set(mode='OBJECT');self.root.select_set(False)
        self.root.scale=(scale,)*3;self.parts=[];self.face=[];self.eyes=[]
        def part(label,rings,s,at,mat,bone):
            o=profile(name+'_'+label,rings,s,at,mat)
            group=o.vertex_groups.new(name=bone);group.add(list(range(len(o.data.vertices))),1,'REPLACE')
            mod=o.modifiers.new('rig','ARMATURE');mod.object=self.root;o.parent=self.root
            self.parts.append(o);return o
        self.part=part
        rabbit=kind=='rabbit'
        part('body',PEAR,(.44,.32,.65),(0,0,.93),skin,'body')
        part('waistcoat',PEAR,(.454,.332,.40),(0,0,1.10),vest if rabbit else cream,'body')
        part('bib',ROUND,(.25,.035,.32),(0,-.335,1.12),cream,'body')
        # Shaped cheek silhouette and muzzle are distinct from the body profile.
        part('head',[(z,r*(1.15 if -.6<z<.1 else 1)) for z,r in ROUND],(.43,.34,.46),(0,-.04,1.89),skin,'head')
        for side,x in [('L',-.26),('R',.26)]:
            part('haunch_'+side,PEAR,(.19,.21,.31),(x,.04,.43),skin,'leg.'+side)
            part('boot_'+side,ROUND,(.19,.30,.12),(x,-.13,.15),cream,'leg.'+side)
            part('arm_'+side,PEAR,(.13,.14,.34),(x*1.8,0,.96),skin,'arm.'+side)
            part('paw_'+side,ROUND,(.15,.15,.16),(x*1.85,-.03,.67),cream,'arm.'+side)
            if rabbit:
                part('ear_'+side,LEAF,(.17,.09,1.05),(x,0,2.12),skin,'ear.'+side)
                part('ear_inner_'+side,LEAF,(.105,.026,.78),(x,-.085,2.28),pink,'ear.'+side)
            self.eyes.append(part('eye_'+side,ROUND,(.115,.055,.16),(x*.80,-.351,2.01),white,'head'))
            eye=part('pupil_'+side,ROUND,(.058,.027,.095),(x*.80,-.401,2.01),dark,'head');self.face.append(eye);self.eyes.append(eye)
            part('glint_'+side,ROUND,(.022,.012,.027),(x*.80-.018,-.425,2.05),white,'head')
            part('cheek_'+side,ROUND,(.17,.09,.12),(x*.50,-.35,1.78),cream,'head')
            brow=part('brow_'+side,ROUND,(.12,.025,.024),(x*.80,-.36,2.23),skin,'head');self.face.append(brow)
        part('nose',LEAF,(.10,.07,.09),(0,-.45,1.81),pink if rabbit else skin,'head')
        self.mouth=part('mouth',ROUND,(.10,.018,.048),(0,-.424,1.70),dark,'head')
        if rabbit:
            part('tail',ROUND,(.18,.18,.19),(0,.34,.73),cream,'body')
            for x in (-.07,.07):part('button',ROUND,(.027,.018,.027),(x,-.35,1.12),pink,'body')
        else:
            part('shell',[(0,.6),(.15,.95),(.6,1),(.9,.63),(1,.02)],(.59,.42,.88),(0,.16,.63),shell,'body')
            # Raised scute seams follow the shell instead of an untextured dome.
            seam=material('shell_ridges',(.55,.64,.21))
            for z,r in [(.85,.53),(1.14,.55),(1.4,.43)]:
                pts=[(r*math.cos(a),.16+.41*math.sin(a),z) for a in [i*math.pi/24 for i in range(25)]]
                o=curve(name+'_scute',pts,.018,seam);o.parent=self.root
        self.identity={'id':name,'species':kind,'skin':list(skin.diffuse_color[:3]),'rig':'profile-armature-v1'}

    def pose(self,action,t,at=(0,0,0),yaw=0,emotion='happy',keyframe=None):
        p=sample(action,t);self.root.location=(at[0],at[1],at[2]+p['lift']);self.root.rotation_euler[2]=yaw
        for b in self.root.pose.bones:
            b.rotation_mode='XYZ';b.rotation_euler=(p.get(b.name,0),0,p['look'] if b.name=='head' else 0)
            if keyframe is not None:b.keyframe_insert('rotation_euler',frame=keyframe)
        # Mouth vertices are at rest coordinates; scale local geometry around mouth centre.
        if not hasattr(self,'_mouth_rest'):self._mouth_rest=[v.co.copy() for v in self.mouth.data.vertices]
        for v,base in zip(self.mouth.data.vertices,self._mouth_rest):
            v.co.z=1.70+(base.z-1.70)*(1+2*p['mouth'])
        if keyframe is not None:
            self.root.keyframe_insert('location',frame=keyframe);self.root.keyframe_insert('rotation_euler',frame=keyframe)
        # Blink and gaze are evaluated from absolute seconds, never accumulated.
        if not hasattr(self,'_eye_rest'):self._eye_rest={o.name:[v.co.copy() for v in o.data.vertices] for o in self.eyes}
        blink=max(.08,min(1,abs((t+len(self.name)*.11)%3.7-1.8)*12))
        for eye in self.eyes:
            for v,base in zip(eye.data.vertices,self._eye_rest[eye.name]):
                v.co.z=2.01+(base.z-2.01)*blink
                v.co.x=base.x+(.018*math.sin(t*1.3) if 'pupil' in eye.name else 0)
        # Expression is a paired head/body pose; face width stays consistent.
        for i,brow in enumerate(self.face[1::2]):
            if not hasattr(self,'_brow_rest'): self._brow_rest={}
            rest=self._brow_rest.setdefault(brow.name,[v.co.copy() for v in brow.data.vertices])
            slope=(.24 if emotion=='sad' else -.15 if emotion=='curious' else 0)*(1 if i==0 else -1)
            for v,base in zip(brow.data.vertices,rest):v.co.z=base.z+slope*(base.x-(-.208 if i==0 else .208))
        self.root['expression']=emotion
        return p


def forest(seed=17):
    rng=random.Random(seed)
    grass=material('meadow',(.22,.40,.23));path=material('path',(.64,.48,.28));bark=material('bark',(.22,.11,.065))
    leaf=[material('leaf'+str(i),c) for i,c in enumerate([(.13,.32,.19),(.26,.48,.24),(.38,.54,.23)])]
    profile('meadow',[(0,1),(.03,1)],(30,30,1),(0,0,-.05),grass,64)
    # Story path runs horizontally in front of a layered woodland.
    profile('trail',[(0,1),(.02,1)],(11,1.5,1),(0,0,0),path,64)
    for i in range(25):
        x,y=rng.uniform(-13,13),rng.uniform(3,13);h=rng.uniform(2.6,5.5)
        profile('trunk',[(0,.18),(.8,.14),(1,.07)],(1,1,h),(x,y,0),bark,10)
        for j in range(3):profile('canopy',LEAF,(1.15+j*.22,1.0,2),(x+j*.28-.3,y,h-1.0+j*.42),leaf[(i+j)%3],12)
    flower=material('flower',(.97,.66,.27));stone=material('stone',(.35,.40,.39))
    for i in range(55):
        x,y=rng.uniform(-10,10),rng.uniform(-3,6)
        if abs(y)<1.4:continue
        profile('fern',LEAF,(.15,.10,.45),(x,y,0),leaf[i%3],6)
        if i%4==0:profile('blossom',ROUND,(.09,.09,.07),(x,y,.43),flower,8)
        if i%9==0:profile('riverstone',ROUND,(.35,.24,.16),(x,y,.12),stone,12)
    # Far hills keep depth without depending on external textures.
    for x in (-13,-5,5,14):profile('hill',ROUND,(8,5,3),(x,17,-.4),leaf[0],20)


def lighting():
    world=bpy.context.scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.65,.79,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.45
    for name,at,power,color,size in [('key',(-3,-4,7),1300,(1,.82,.59),5),('fill',(4,-1,5),700,(.64,.81,1),4),('rim',(1,5,6),1600,(1,.77,.42),3)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size
        obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj);obj.location=at
        obj.rotation_euler=(Vector((0,0,1))-obj.location).to_track_quat('-Z','Y').to_euler()


def camera(at,target,lens=48):
    data=bpy.data.cameras.new('story_camera');o=bpy.data.objects.new('story_camera',data)
    bpy.context.collection.objects.link(o);o.location=at;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    data.lens=lens;bpy.context.scene.camera=o;return o


def frame_camera(cam,subjects,kind='medium',progress=0,track=(0,0,0)):
    """Fit cast scale and width; close-ups target scaled heads, not world height."""
    center=sum((Vector(o.root.location) for o in subjects),Vector())/len(subjects)+Vector(track)
    if kind=='close':
        actor=subjects[0];scale=actor.root.scale.z
        target=center+Vector((0,0,1.65*scale))
        cam.location=center+Vector((.18,-3.7*scale,2.3*scale))
    else:
        left=min(o.root.location.x-.65*o.root.scale.x for o in subjects)
        right=max(o.root.location.x+.65*o.root.scale.x for o in subjects)
        height=max((3.35 if o.kind=='rabbit' else 2.5)*o.root.scale.z for o in subjects)
        distance=max(10.5 if kind=='wide' else 9.8,(right-left)*1.7)
        distance*=1-.025*progress
        target=center+Vector((0,0,height*.34))
        cam.location=center+Vector((distance*.09,-distance,height*.90))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()


def projected_bounds(obj,cam,scene):
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();evaluated=obj.evaluated_get(deps)
    pts=[world_to_camera_view(scene,cam,evaluated.matrix_world@Vector(p)) for p in evaluated.bound_box]
    return [min(p.x for p in pts),1-max(p.y for p in pts),max(p.x for p in pts),1-min(p.y for p in pts)]


def hand_position(actor,side='R'):
    bpy.context.view_layer.update()
    bone=actor.root.pose.bones['arm.'+side]
    return actor.root.matrix_world @ bone.matrix @ Vector((0,bone.length,0))


def hold_prop(actor,prop,side='R',offset=(0,0,0)):
    """Call after posing on each frame; explicitly bind prop to evaluated hand tip."""
    prop.location=hand_position(actor,side)+Vector(offset)
    return prop.location.copy()


def interaction_error(actor,prop,side='R'):
    """Measured contact error in metres, suitable for interaction metadata."""
    return (hand_position(actor,side)-prop.matrix_world.translation).length


def configure_renderer(scene=None,samples=64,require_gpu=False):
    """Probe actual devices; log selection. Compatible with the CPU and GPU images."""
    import os
    scene=scene or bpy.context.scene
    require_gpu=require_gpu or os.environ.get('FACELESS_GPU_REQUIRED')=='1'
    requested=os.environ.get('FACELESS_BLENDER_BACKEND','AUTO')
    backends=[requested] if requested in ('OPTIX','CUDA') else ['OPTIX','CUDA']
    preferences=bpy.context.preferences.addons['cycles'].preferences
    for backend in backends:
        try:
            preferences.compute_device_type=backend;preferences.get_devices()
            devices=[d for d in preferences.devices if d.type==backend]
            if not devices:continue
            for device in preferences.devices:device.use=device.type==backend
            scene.render.engine='CYCLES';scene.cycles.device='GPU';scene.cycles.samples=samples
            scene.cycles.use_denoising=True
            if hasattr(scene.cycles,'denoising_use_gpu'):scene.cycles.denoising_use_gpu=True
            result={'backend':backend,'devices':[d.name for d in devices],'engine':'CYCLES','device':'GPU'}
            print('BLENDER_RENDER_DEVICE='+str(result),flush=True)
            return result
        except (TypeError,ValueError,RuntimeError):continue
    if require_gpu:raise RuntimeError('Requested GPU render has no supported Cycles device')
    scene.render.engine='BLENDER_EEVEE_NEXT' if bpy.app.version>=(4,2,0) else 'BLENDER_EEVEE'
    if hasattr(scene,'eevee'):scene.eevee.taa_render_samples=8;scene.eevee.use_gtao=True
    result={'backend':'CPU','devices':[],'engine':scene.render.engine,'device':'CPU fallback'}
    print('BLENDER_RENDER_DEVICE='+str(result),flush=True)
    return result
