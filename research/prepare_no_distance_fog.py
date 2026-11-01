from pathlib import Path
import sys, shutil, struct, json, hashlib
sys.path.insert(0,str(Path(__file__).parent/'python-deps'))
import pefile

base=Path('outputs/Amok-2160p-Widescreen-Fixed-Test')
target=Path('outputs/Amok-2160p-No-Distance-Fog-Test')
assert not target.exists(), 'Do not overwrite a played build.'
original=(base/'AMOK.EXE').read_bytes()
data=bytearray(original)
pe=pefile.PE(data=original)
changes=[]
for address,old,kind in ((0x411f5b,0x2000,'terrain'),(0x41200a,0x1000,'objects')):
    off=pe.get_offset_from_rva(address-pe.OPTIONAL_HEADER.ImageBase)
    expected=b'\xb8'+struct.pack('<I',old)
    replacement=b'\xb8'+struct.pack('<I',0)
    assert data[off:off+5]==expected
    data[off:off+5]=replacement
    changes.append(dict(address=hex(address),original=expected.hex(),replacement=replacement.hex(),
                        reason=f'Use the clear palette row at every {kind} distance'))
# Keep all fade-length denominators, draw limits and lookup table sizes intact.
assert len(data)==len(original)
allowed=set()
for change in changes:
    off=pe.get_offset_from_rva(int(change['address'],16)-pe.OPTIONAL_HEADER.ImageBase)
    allowed.update(range(off,off+5))
assert all(i in allowed for i,(a,b) in enumerate(zip(original,data)) if a!=b)
shutil.copytree(base,target)
(target/'AMOK.EXE').write_bytes(data)
manifest=target/'widescreen-patches.json'
manifest.write_text(json.dumps(json.loads(manifest.read_text(encoding='utf-8-sig'))+changes,indent=2))
v=json.loads((target/'validation.json').read_text(encoding='utf-8-sig'))
v.update(sha256=hashlib.sha256(data).hexdigest(),runtime_surface_verified=False,
         distance_fog_removed_player_verified=False,hard_draw_distance_extended=False,
         zero_fade_step_patch_verified=True)
(target/'validation.json').write_text(json.dumps(v,indent=2))
(target/'README.md').write_text('''# AMOK: no distance fog comparison

Launch Play-Amok-4K-No-Distance-Fog.cmd from the parent outputs folder.

This comparison uses the clear palette row for terrain and objects at every
rendered distance. The original maximum drawing limits remain in place, so
distant terrain edges and object pop-in may be more visible. Level lighting,
underwater colors and the sky are retained.

Built from the confirmed 4K widescreen version with its working controls,
smaller HUD, camera overlay correction and terrain alignment repair.
Visual testing is pending. Play-Amok-4K-Widescreen-Fixed.cmd launches the
confirmed version with the original fog.
''',encoding='utf-8')
print('Created no-distance-fog comparison; only the two fade-step instructions changed.')
