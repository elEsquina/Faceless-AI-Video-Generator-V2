import bpy, sys, os
from math import radians

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
out = '/workspace/output/blender.png'
if '--output' in argv:
    out = argv[argv.index('--output')+1]
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.object
obj.rotation_euler = (radians(24), 0, radians(36))
mat = bpy.data.materials.new(name='Cyan')
mat.diffuse_color = (0.03, 0.45, 0.8, 1)
obj.data.materials.append(mat)
world = bpy.context.scene.world
world.color = (0.10, 0.10, 0.10)
bpy.ops.object.camera_add(location=(4, -5, 3))
cam = bpy.context.object
from mathutils import Vector
cam.rotation_euler = (Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.context.scene.camera = cam
bpy.ops.object.light_add(type='AREA', location=(1,-3,5))
bpy.context.object.data.energy = 800
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 8
scene.cycles.use_denoising = False
for vl in scene.view_layers:
    if hasattr(vl, 'cycles') and hasattr(vl.cycles, 'use_denoising'):
        vl.cycles.use_denoising = False
used = 'CPU'
try:
    cycles = bpy.context.preferences.addons['cycles'].preferences
    for backend in ('OPTIX', 'CUDA'):
        try:
            cycles.compute_device_type = backend
            cycles.get_devices()
            gpu_devs = [d for d in cycles.devices if d.type != 'CPU']
            if gpu_devs:
                for d in cycles.devices:
                    d.use = d.type != 'CPU'
                scene.cycles.device = 'GPU'
                used = backend + ': ' + ', '.join(d.name for d in gpu_devs)
                break
        except Exception as exc:
            print('GPU probe', backend, str(exc))
except Exception as exc:
    print('GPU unavailable:', exc)
print('BLENDER_RENDER_DEVICE=' + used, flush=True)
scene.render.resolution_x = 320
scene.render.resolution_y = 180
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = out
os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.render.render(write_still=True)
