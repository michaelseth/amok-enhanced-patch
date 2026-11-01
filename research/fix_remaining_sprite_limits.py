from pathlib import Path
import sys, struct, json, hashlib, shutil
sys.path.insert(0, str(Path(__file__).parent / 'python-deps'))
import pefile

folder = Path('outputs/Amok-2160p-Extended-Scene-Test')
exe = folder / 'AMOK.EXE'
original = exe.read_bytes()
pe = pefile.PE(data=original)
data = bytearray(original)
specs = [
    (0x4157ad, '81ffb01f0000', '81ff603f0000', 'Double static sprite forward projection cutoff'),
    (0x41599f, '81fe00004000', '81fe00000001', 'Double active object drawing radius using squared distance'),
    (0x426718, '817db400640000', '817db400900100', 'Match scenery retirement radius to extended update radius'),
]
changes = []
for address, old, new, reason in specs:
    offset = pe.get_offset_from_rva(address - 0x400000)
    assert data[offset:offset+len(bytes.fromhex(old))] == bytes.fromhex(old)
    data[offset:offset+len(bytes.fromhex(new))] = bytes.fromhex(new)
    changes.append(dict(address=hex(address), original=old, replacement=new, reason=reason))
assert 0x1000000 == 4 * 0x400000
assert 0x3f60 == 2 * 0x1fb0
assert 0x19000 > 294**2
backup = Path('work/AMOK-extended-scene-before-object-limit-fix.exe')
assert not backup.exists()
backup.write_bytes(original)
exe.write_bytes(data)
manifest = folder / 'widescreen-patches.json'
patches = json.loads(manifest.read_text(encoding='utf-8-sig')) + changes
manifest.write_text(json.dumps(patches, indent=2))
result = pefile.PE(str(exe))
for change in patches:
    offset = result.get_offset_from_rva(int(change['address'], 16)-0x400000)
    expected = bytes.fromhex(change['replacement'])
    assert result.__data__[offset:offset+len(expected)] == expected, change
vpath = folder / 'validation.json'
v = json.loads(vpath.read_text(encoding='utf-8-sig'))
v.update(sha256=hashlib.sha256(data).hexdigest(), scene_patch_bytes_verified=40,
         scenery_row_fix_player_report='Better visibility and less flickering/misalignment; sprites still cut off before terrain',
         additional_sprite_limits_patch_verified=True, scenery_retirement_squared_radius=0x19000,
         active_object_draw_squared_radius=0x1000000, static_sprite_forward_cutoff=0x3f60,
         extended_scene_player_verified=False, runtime_surface_verified=False)
vpath.write_text(json.dumps(v, indent=2))
with (folder / 'README.md').open('a', encoding='utf-8') as f:
    f.write('\nAdditional object limits: doubled the static forward cutoff and active\n'
            'object drawing radius. Scenery retirement now matches its extended\n'
            'update radius and exceeds activation radius, preventing repeated\n'
            'activation/removal in the added range. Player retest pending.\n')
source = Path('outputs/Amok-Enhancement-Source')
shutil.copy2(__file__, source / Path(__file__).name)
with (source / 'BUILD-NOTES.md').open('a', encoding='utf-8') as f:
    f.write('\nRun fix_remaining_sprite_limits.py after fix_scene_row_stride.py.\n'
            '0x4157ad: static forward gate 0x1fb0 to 0x3f60.\n'
            '0x41599f: active render squared distance 0x400000 to 0x1000000.\n'
            '0x426718: scenery retirement squared radius 0x6400 to 0x19000,\n'
            'matching 0x425eb8 update gate and exceeding activation 294 squared.\n'
            'All manifest patch bytes verified; visual retest pending.\n')
print('Three remaining object limits corrected; 40 scene patch bytes verified.')
