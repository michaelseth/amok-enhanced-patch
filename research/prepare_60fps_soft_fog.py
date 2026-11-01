from pathlib import Path
import sys,shutil,struct,json,hashlib
sys.path.insert(0,str(Path(__file__).parent/'python-deps'))
import pefile
base=Path('outputs/Amok-2160p-Fast-Soft-Fog-Test')
target=Path('outputs/Amok-2160p-60FPS-Soft-Fog-Test')
assert not target.exists()
data=bytearray((base/'AMOK.EXE').read_bytes());pe=pefile.PE(data=data)
changes=[]
for address,old in ((0x417e34,26),(0x417e40,40)):
 off=pe.get_offset_from_rva(address-0x400000)
 expected=bytes.fromhex('c705543a5d00')+struct.pack('<I',old)
 replacement=bytes.fromhex('c705543a5d00')+struct.pack('<I',60)
 assert data[off:off+10]==expected
 data[off:off+10]=replacement
 changes.append(dict(address=hex(address),original=expected.hex(),replacement=replacement.hex(),
                     reason='Raise mission frame limit to 60 while retaining elapsed-time simulation scaling'))
# Timing/scaling function is byte-identical to the prior confirmed implementation.
offset=pe.get_offset_from_rva(0x424540-0x400000)
assert data[offset:offset+0x200]==(base/'AMOK.EXE').read_bytes()[offset:offset+0x200]
shutil.copytree(base,target)
(target/'AMOK.EXE').write_bytes(data)
m=target/'widescreen-patches.json'
m.write_text(json.dumps(json.loads(m.read_text(encoding='utf-8-sig'))+changes,indent=2))
vpath=target/'validation.json';v=json.loads(vpath.read_text(encoding='utf-8-sig'))
v.update(sha256=hashlib.sha256(data).hexdigest(),runtime_surface_verified=False,
 mission_frame_limit=60,original_mission_frame_limits=[26,40],
 elapsed_time_scaling_unchanged_verified=True,motion_60fps_player_verified=False,
 previous_player_report='Strafing good; turning a little jerky; forward/back mostly good')
vpath.write_text(json.dumps(v,indent=2))
(target/'README.md').write_text('''# AMOK: 4K extended distance and subtle fog, 60 FPS test

Launch Play-Amok-4K-60FPS-Soft-Fog.cmd from the parent outputs folder.

Retains the faster terrain renderer, extended distance, approved fog and
Xbox controls. The two mission frame limits are raised from 26/40 to 60 FPS.
The elapsed-time simulation scaling function is unchanged. Actual frame rate
depends on rendering time. Check turning smoothness and normal movement speed.
Visual gameplay confirmation is pending; full playthrough remains untested.
Terrain-range-status.txt records frame intervals and terrain accuracy checks.
''',encoding='utf-8')
source=Path('outputs/Amok-Enhancement-Source')
shutil.copy2(__file__,source/Path(__file__).name)
with (source/'BUILD-NOTES.md').open('a',encoding='utf-8') as f:
 f.write('\n60 FPS comparison: prepare_60fps_soft_fog.py changes only mission\n'
         'frame limit assignments at 0x417e34 (26) and 0x417e40 (40) to 60.\n'
         'Elapsed-time simulation scaler at 0x424540 remains byte-identical.\n'
         'Previous renderer intervals averaged ~24 ms; motion retest pending.\n')
print('Prepared 60 FPS mission comparison; elapsed-time scaler unchanged.')
