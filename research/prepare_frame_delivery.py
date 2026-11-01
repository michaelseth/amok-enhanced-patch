from pathlib import Path
import shutil,json,hashlib
base=Path('outputs/Amok-2160p-Ray-Precision-Test')
target=Path('outputs/Amok-2160p-Frame-Delivery-Test')
assert not target.exists(), 'Do not overwrite a played build.'
shutil.copytree(base,target)
ini=target/'ddraw.ini'
text=ini.read_text(encoding='utf-8-sig')
assert 'maxgameticks=60' in text and 'singlecpu=' not in text
text=text.replace('maxgameticks=60','maxgameticks=-1')+'\nsinglecpu=false\n'
ini.write_text(text,encoding='utf-8')
for name in ('AMOK.EXE','AMOKMOD.dll'):
 assert (base/name).read_bytes()==(target/name).read_bytes()
vpath=target/'validation.json'
v=json.loads(vpath.read_text(encoding='utf-8-sig'))
v.update(frame_delivery_player_verified=False,wrapper_tick_limiter_disabled=True,
 wrapper_cpu0_affinity_disabled=True,game_mission_frame_limit=60,
 game_executable_and_helper_unchanged_verified=True)
vpath.write_text(json.dumps(v,indent=2))
(target/'README.md').write_text('''# AMOK: frame delivery comparison

Based on the confirmed 4K ray-precision build. Game EXE and helper DLL are
byte-identical. Controls, draw range, fog, alignment and polygon fixes retained.
Display wrapper maxgameticks=-1 removes its duplicate game-tick limiter;
singlecpu=false removes its forced CPU0 affinity. The game retains its own
60 FPS mission cap and elapsed-time movement scaling; presentation cap stays 60.
Runtime performance and player checks are pending. Check moving, turning,
firing, sound and menus for normal speed and smoothness.
''',encoding='utf-8')
source=Path('outputs/Amok-Enhancement-Source')
shutil.copy2(__file__,source/Path(__file__).name)
with (source/'BUILD-NOTES.md').open('a',encoding='utf-8') as f:
 f.write('\nFrame delivery comparison: prepare_frame_delivery.py keeps EXE/DLL identical. '
         'ddraw.ini maxgameticks=-1 and singlecpu=false; own game mission limit remains 60. '
         'Wrapper documented defaults/config: https://github.com/FunkyFr3sh/cnc-ddraw/blob/master/src/config.c . '
         'Runtime measurements and gameplay confirmation pending.\n')
print('Prepared frame delivery comparison; EXE/helper byte-identical.')
