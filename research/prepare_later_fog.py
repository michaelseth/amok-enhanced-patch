from pathlib import Path
import sys, shutil, struct, json, hashlib
sys.path.insert(0,str(Path(__file__).parent/'python-deps'))
import pefile

base=Path('outputs/Amok-2160p-Widescreen-Fixed-Test')
target=Path('outputs/Amok-2160p-Later-Fog-Test')
assert not target.exists(), 'Do not overwrite a played test build.'
source=(base/'AMOK.EXE').read_bytes()
pe=pefile.PE(data=source)
data=bytearray(source)
changes=[]
profiles=[]
for address,kind in ((0x48a956,'terrain'),(0x48a960,'objects')):
    off=pe.get_offset_from_rva(address-pe.OPTIONAL_HEADER.ImageBase)
    old=struct.unpack_from('<5h',data,off)
    expected=(55,60,80,65,65) if kind=='terrain' else (64,48,44,48,44)
    assert old==expected
    # Terrain stores the fade length ending at sample 140; objects store
    # the clear range preceding a fade ending at depth index 78.
    new=tuple((n+1)//2 for n in old) if kind=='terrain' else tuple(n+(78-n)//2 for n in old)
    replacement=struct.pack('<5h',*new)
    data[off:off+10]=replacement
    changes.append(dict(address=hex(address),original=struct.pack('<5h',*old).hex(),replacement=replacement.hex(),
                        reason=f'Delay {kind} fog onset while retaining the original fade endpoint'))
    for i,(a,b) in enumerate(zip(old,new)):
        start_old=140-a if kind=='terrain' else a
        start_new=140-b if kind=='terrain' else b
        end=140 if kind=='terrain' else 78
        assert 0<=start_old<start_new<end
        # All generated palette row indices remain inside their existing tables.
        rows=32 if kind=='terrain' else 16
        fade_length=end-start_new
        indices=[(j*((rows*256)//fade_length))>>8 for j in range(fade_length)]
        assert min(indices)>=0 and max(indices)<rows
        profiles.append(dict(kind=kind,profile=i,fog_start_before=start_old,fog_start_after=start_new,fog_end=end))
shutil.copytree(base,target)
(target/'AMOK.EXE').write_bytes(data)
manifest=target/'widescreen-patches.json'
manifest.write_text(json.dumps(json.loads(manifest.read_text(encoding='utf-8-sig'))+changes,indent=2))
v=json.loads((target/'validation.json').read_text(encoding='utf-8-sig'))
v.update(sha256=hashlib.sha256(data).hexdigest(),runtime_surface_verified=False,
         later_fog_player_verified=False,fog_profile_bounds_verified=True,
         hard_draw_distance_extended=False,fog_profiles=profiles,
         inherited_confirmed_controls_camera_and_terrain_patches=True)
(target/'validation.json').write_text(json.dumps(v,indent=2))
(target/'README.md').write_text('''# AMOK: later-fog comparison build

Launch Play-Amok-4K-Later-Fog.cmd from the parent outputs folder.

Based on the confirmed 3840x2160 widescreen build, with the same controls,
camera overlay correction, smaller HUD and terrain alignment repair.

Terrain fog begins farther away and fades across roughly half its original
range. Object fog also starts farther away. Both fades end at the original
limits. This changes visibility, not the hard terrain/object drawing limits.
Palette lookup bounds were checked. Visual and mission testing is pending.

The confirmed build is available through Play-Amok-4K-Widescreen-Fixed.cmd.
Original game files in C:/Amok are unchanged.
''',encoding='utf-8')
print('Created separate later-fog build; all five terrain and object profiles checked.')
print(json.dumps(profiles))
