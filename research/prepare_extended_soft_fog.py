from pathlib import Path
import sys, shutil, struct, json, hashlib
sys.path.insert(0,str(Path(__file__).parent/'python-deps'))
import pefile

base=Path('outputs/Amok-2160p-Extended-Scene-Test')
target=Path('outputs/Amok-2160p-Extended-Soft-Fog-Test')
assert not target.exists(), 'Do not overwrite a played build.'
data=bytearray((base/'AMOK.EXE').read_bytes());pe=pefile.PE(data=data)
far=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.farfix')
table=0x400000+far.VirtualAddress+0x2000
changes=[]
for j,palette in enumerate((0x4fa698,0x4fd6b8,0x4fe6b8)):
 address=table+j*148*4;off=pe.get_offset_from_rva(address-0x400000)
 old=struct.pack('<148I',*([palette]*148))
 assert data[off:off+len(old)]==old
 rows=[]
 for depth in range(148):
  t=max(0.0,min(1.0,(depth-118)/29.0))
  rows.append(int(15*t*t*(3-2*t)+0.5))
 assert rows[:119]==[0]*119 and rows[-1]==15
 assert all(0<=a<=b<=15 for a,b in zip(rows,rows[1:]))
 new=struct.pack('<148I',*[palette+r*256 for r in rows])
 data[off:off+len(new)]=new
 changes.append(dict(address=hex(address),original=old.hex(),replacement=new.hex(),
                     reason='Ease sprite fog into final extended depth range'))
terrain_rows=[]
for depth in range(280):
 t=max(0.0,min(1.0,(depth-220)/59.0))
 terrain_rows.append(int(31*t*t*(3-2*t)+0.5))
assert terrain_rows[:221]==[0]*221 and terrain_rows[-1]==31
assert all(0<=a<=b<=31 for a,b in zip(terrain_rows,terrain_rows[1:]))
shutil.copytree(base,target)
(target/'AMOK.EXE').write_bytes(data)
shutil.copy2('work/AMOKMOD-soft-fog.dll',target/'AMOKMOD.dll')
manifest=target/'widescreen-patches.json'
manifest.write_text(json.dumps(json.loads(manifest.read_text(encoding='utf-8-sig'))+changes,indent=2))
v=json.loads((target/'validation.json').read_text(encoding='utf-8-sig'))
v.update(sha256=hashlib.sha256(data).hexdigest(), runtime_surface_verified=False,
 soft_fog_player_verified=False,soft_fog_palette_bounds_verified=True,
 terrain_fog_start_sample=220,terrain_fog_end_sample=279,
 sprite_fog_start_depth=118,sprite_fog_end_depth=147,
 fog_curve='smoothstep with native level fog palettes',
 helper_sha256=hashlib.sha256((target/'AMOKMOD.dll').read_bytes()).hexdigest())
(target/'validation.json').write_text(json.dumps(v,indent=2))
(target/'README.md').write_text('''# AMOK: extended distance with subtle edge fog

Launch Play-Amok-4K-Extended-Soft-Fog.cmd in the parent outputs folder.

Uses the visually confirmed 4K extended-distance build and controller controls.
Terrain stays clear for roughly the first 79% of the extended drawing range,
then eases into the level's original fog color near the cutoff. Sprite fog
uses a corresponding fade at the far end of its expanded depth range.
The fade uses the game's palette steps, so fine color banding may remain.
Visual confirmation is pending. Saves/settings are copied from the latest build.

Play-Amok-4K-Extended-Scene.cmd retains the confirmed fog-free version.
''',encoding='utf-8')
print('Created extended soft-fog build; terrain and sprite palette bounds verified.')
