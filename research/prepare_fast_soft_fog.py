from pathlib import Path
import shutil,json,hashlib
base=Path('outputs/Amok-2160p-Extended-Soft-Fog-Test')
target=Path('outputs/Amok-2160p-Fast-Soft-Fog-Test')
assert not target.exists()
shutil.copytree(base,target)
shutil.copy2('work/AMOKMOD-fast-fog.dll',target/'AMOKMOD.dll')
vpath=target/'validation.json'
v=json.loads(vpath.read_text(encoding='utf-8-sig'))
v.update(runtime_surface_verified=False,soft_fog_player_verified=True,
 fast_terrain_player_verified=False,decoded_terrain_synthetic_parity_verified=True,
 decoded_terrain_map_change_and_level_invalidation_verified=True,
 helper_sha256=hashlib.sha256((target/'AMOKMOD.dll').read_bytes()).hexdigest(),
 previous_player_report='Fog looks great; terrain feels jerky during both movement and turning')
vpath.write_text(json.dumps(v,indent=2))
(target/'README.md').write_text('''# AMOK: faster extended terrain with subtle edge fog

Launch Play-Amok-4K-Fast-Soft-Fog.cmd from the parent outputs folder.

Retains the 4K surface, extended draw distance, controls and approved fog.
The terrain sampler uses predecoded terrain and refreshes changed map chunks
each frame. Level loading invalidates the cached source. Sample lookup avoids
per-sample C calls. Synthetic parity and refresh tests passed; visual motion
confirmation is pending. Terrain-range-status.txt records real-level parity
and frame intervals. Full playthrough remains untested.

Play-Amok-4K-Extended-Soft-Fog.cmd launches the preceding version.
''',encoding='utf-8')
source=Path('outputs/Amok-Enhancement-Source')
for name in ('amok_far_terrain.c','amok_fast_terrain.c','test_fast_terrain.c','prepare_fast_soft_fog.py'):
 shutil.copy2(Path('work')/name,source/name)
with (source/'BUILD-NOTES.md').open('a',encoding='utf-8') as f:
 f.write('\nFast terrain comparison: add -DAMOK_FAST_TERRAIN to the soft-fog DLL\n'
         'compile flags, produce work/AMOKMOD-fast-fog.dll, and run\n'
         'prepare_fast_soft_fog.py once. Loader hook 0x4117a4 invalidates the\n'
         '8 MiB decoded terrain; renderer entry 0x42036c refreshes changed map\n'
         'chunks before drawing. Two sampler hooks use native cached lookup.\n'
         'Synthetic reference parity including boundaries, map changes and\n'
         'level invalidation passed. Real mission parity and motion pending.\n')
print('Prepared separate fast soft-fog comparison; EXE and fog settings unchanged.')
