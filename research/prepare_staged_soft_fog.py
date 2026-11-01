from pathlib import Path
import shutil,json,hashlib
base=Path('outputs/Amok-2160p-60FPS-Soft-Fog-Test')
target=Path('outputs/Amok-2160p-Staged-Soft-Fog-Test')
assert not target.exists()
shutil.copytree(base,target)
shutil.copy2('work/AMOKMOD-stage-fog.dll',target/'AMOKMOD.dll')
vpath=target/'validation.json';v=json.loads(vpath.read_text(encoding='utf-8-sig'))
v.update(runtime_surface_verified=False,native_terrain_staging_player_verified=False,
 terrain_staging_synthetic_pixel_pairs_verified=4147200,
 terrain_staging_synthetic_occlusion_pointers_verified=270720,
 helper_sha256=hashlib.sha256((target/'AMOKMOD.dll').read_bytes()).hexdigest(),
 previous_player_report='Turning remains stuttery; raising frame limit did not resolve it')
vpath.write_text(json.dumps(v,indent=2))
(target/'README.md').write_text('''# AMOK: 4K terrain drawing performance test

Launch Play-Amok-4K-Staged-Soft-Fog.cmd in the parent outputs folder.

Full native 4K terrain pixels, extended range, fog and controls are retained.
Terrain columns draw into contiguous memory, then transpose to the native
framebuffer. Sprite occlusion addresses are converted to native coordinates.
The first frame compares every pixel and occlusion entry with direct drawing;
the optimization automatically disables itself if that comparison fails.
Frame intervals and terrain drawing cost are logged in terrain-range-status.txt.
Synthetic pixel and occlusion tests passed. Real mission validation pending.
''',encoding='utf-8')
source=Path('outputs/Amok-Enhancement-Source')
for name in ('amok_fast_terrain.c','amok_terrain_staging.c','test_terrain_staging.c','prepare_staged_soft_fog.py'):
 shutil.copy2(Path('work')/name,source/name)
with (source/'BUILD-NOTES.md').open('a',encoding='utf-8') as f:
 f.write('\nNative terrain staging comparison: add -msse2 -DAMOK_RENDER_PROFILE\n'
         '-DAMOK_TERRAIN_STAGE to fast soft-fog helper flags. Produce\n'
         'work/AMOKMOD-stage-fog.dll; run prepare_staged_soft_fog.py once.\n'
         'Native dimensions and world sample geometry retained. First-frame\n'
         'direct/staged pixel and occlusion comparison automatically reverts\n'
         'optimization on mismatches. Synthetic 4,147,200 pixel pairs and\n'
         '270,720 occlusion pointer conversions verified. Runtime pending.\n')
print('Prepared full native 4K terrain staging comparison with automatic parity check.')
