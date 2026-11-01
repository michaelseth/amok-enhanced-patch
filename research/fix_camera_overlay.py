from pathlib import Path
import sys, struct, json, hashlib
sys.path.insert(0, str(Path(__file__).parent/'python-deps'))
import pefile

folder=Path('outputs/Amok-2160p-Widescreen-Fixed-Test')
exe=folder/'AMOK.EXE'
data=bytearray(exe.read_bytes())
pe=pefile.PE(data=bytes(data))
changes=[]
def patch(va, old, new, reason):
    assert len(old)==len(new)
    off=pe.get_offset_from_rva(va-pe.OPTIONAL_HEADER.ImageBase)
    assert data[off:off+len(old)] in (old,new), (hex(va),data[off:off+len(old)].hex())
    data[off:off+len(new)]=new
    changes.append(dict(address=hex(va),original=old.hex(),replacement=new.hex(),reason=reason))

# The compass and waypoint share the stack-local Y row. Their original row
# ignores the F1 camera profile, whereas the aiming baseline includes it.
# Profile (distance, pitch, elevation) -> 4*pitch + 6*camera elevation.
profiles=[(64,-30,80),(54,-72,0),(160,-256,66)]
def baseline(p):
    distance,pitch,elevation=p
    return 4*pitch+6*(30+((distance*elevation)>>8))
deltas=[baseline(p)-baseline(profiles[0]) for p in profiles]
assert deltas==[0,-288,-778]

# Preserve ECX and flags, select the profile correction, convert from the
# game's 1/16-pixel projection units, then replace only the shared Y store.
base=0x460080
code=bytearray(); labels={}; branches=[]
def emit(h): code.extend(bytes.fromhex(h))
def label(name): labels[name]=len(code)
def branch(op,name):
    emit(op); branches.append((len(code),name)); code.append(0)
emit('9c51 0fbf4a6c 83f901')
branch('75','mode2')
emit('b9');code.extend(struct.pack('<i',deltas[1]));branch('eb','apply')
label('mode2');emit('83f902');branch('75','done')
emit('b9');code.extend(struct.pack('<i',deltas[2]))
label('apply');emit('0faf0dac004900 c1f90c 01c8')
label('done');emit('599d 6689442404')
emit('e9');code.extend(struct.pack('<i',0x4143a7-(base+len(code)+4)))
for pos,name in branches:
    code[pos]= (labels[name]-(pos+1)) & 255
assert base+len(code)<0x460100
backup=Path('work/AMOK-widescreen-before-overlay.exe')
if not backup.exists(): backup.write_bytes(data)
patch(base,b'\0'*len(code),bytes(code),'Correct compass/waypoint row for the selected F1 camera profile')
patch(0x4143a2,bytes.fromhex('6689442404'),b'\xe9'+struct.pack('<i',base-(0x4143a2+5)), 'Route shared compass/waypoint vertical position through camera correction')
# This independent local scale controls the ammo, health and radar panel.
# Keep 3D projection and aiming/compass scale unchanged.
patch(0x414ab2,bytes.fromhex('66a1ac004900'),bytes.fromhex('66b800099090'),'Restore main HUD to the confirmed 4:3 build scale (2304)')
for focal in (256,512,640,1536,2304,3072):
    rows=[88*focal//256+(delta*focal>>12) for delta in deltas]
    assert rows[0]==88*focal//256
    assert rows[2]<rows[1]<rows[0]
assert [d*3072>>12 for d in deltas]==[0,-216,-584]
exe.write_bytes(data)
manifest=folder/'widescreen-patches.json'
old=json.loads(manifest.read_text())
addresses={p['address'] for p in changes}
manifest.write_text(json.dumps([p for p in old if p['address'] not in addresses]+changes,indent=2))
validation=folder/'validation.json'
v=json.loads(validation.read_text())
v.update(sha256=hashlib.sha256(data).hexdigest(),main_hud_scale=2304,
         compass_camera_profile_offsets_4k=[0,-216,-584],
         compass_camera_patch_arithmetic_verified=True,
         alternate_camera_compass_alignment_player_verified=False)
validation.write_text(json.dumps(v,indent=2))
print('Installed camera overlay correction and restored main HUD scale; default compass position is unchanged.')
