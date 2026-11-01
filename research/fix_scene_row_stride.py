from pathlib import Path
import sys, json, hashlib, shutil
sys.path.insert(0, str(Path(__file__).parent / 'python-deps'))
import pefile

folder = Path('outputs/Amok-2160p-Extended-Scene-Test')
exe = folder / 'AMOK.EXE'
original = exe.read_bytes()
pe = pefile.PE(data=original)
data = bytearray(original)
changes = []
for address, old, new in [(0x413c80, '83c734', '83c72c'),
                          (0x413c83, '83c334', '83c32c')]:
    offset = pe.get_offset_from_rva(address - pe.OPTIONAL_HEADER.ImageBase)
    assert data[offset:offset+3] == bytes.fromhex(old)
    data[offset:offset+3] = bytes.fromhex(new)
    changes.append(dict(address=hex(address), original=old, replacement=new,
                        reason='Correct five-column scenery scan map row stride'))

# Every descriptor must read the map chunk whose coordinates it projects.
for start in (0, 17, 85, 170):
    cursor = start
    for row in range(5):
        for column in range(5):
            assert cursor == start + row * 16 + column
            cursor += 1
        cursor += 0x2c // 4

backup = Path('work/AMOK-extended-scene-before-row-fix.exe')
assert not backup.exists()
backup.write_bytes(original)
exe.write_bytes(data)
manifest = folder / 'widescreen-patches.json'
patches = json.loads(manifest.read_text(encoding='utf-8-sig')) + changes
manifest.write_text(json.dumps(patches, indent=2))
reloaded = pefile.PE(str(exe))
for change in patches:
    offset = reloaded.get_offset_from_rva(int(change['address'], 16)-0x400000)
    expected = bytes.fromhex(change['replacement'])
    assert reloaded.__data__[offset:offset+len(expected)] == expected, change
validation = folder / 'validation.json'
v = json.loads(validation.read_text(encoding='utf-8-sig'))
v.update(sha256=hashlib.sha256(data).hexdigest(), scenery_row_stride_fix_verified=True,
         scenery_scan_map_row_chunks=16, extended_scene_player_verified=False,
         previous_scene_player_report='Movement smooth, but fewer sprites/enemies visible',
         scene_patch_bytes_verified=37, runtime_surface_verified=False)
validation.write_text(json.dumps(v, indent=2))
with (folder / 'README.md').open('a', encoding='utf-8') as f:
    f.write('\nScenery scan row correction: the five-column scan now advances through\n'
            'the original 16-column map correctly. Visual retesting is pending.\n')
source = Path('outputs/Amok-Enhancement-Source')
for name in ('prepare_extended_scene.py', 'fix_scene_row_stride.py'):
    shutil.copy2(Path('work') / name, source / name)
with (source / 'BUILD-NOTES.md').open('a', encoding='utf-8') as f:
    f.write('\nScenery visibility regression: enlarged 5x5 scan retained the original\n'
            'three-column row remainder (52 bytes), skipping two chunks per row.\n'
            'Corrected 0x413c80 and 0x413c83 to 44 bytes: 5*4+44=16*4.\n'
            'All final manifest patches and the scan coordinate model verified;\n'
            'player retest pending. fix_scene_row_stride.py updates a played build\n'
            'without replacing settings or saves.\n')
print('Corrected both map row strides; all patch bytes and scan coordinates verified.')
