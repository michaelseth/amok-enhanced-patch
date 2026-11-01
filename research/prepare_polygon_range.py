from pathlib import Path
import sys, struct, json, shutil, hashlib
sys.path.insert(0, str(Path(__file__).parent / 'python-deps'))
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

base = Path('outputs/Amok-2160p-Staged-Soft-Fog-Test')
target = Path('outputs/Amok-2160p-Polygon-Range-Test')
assert not target.exists(), 'Do not overwrite a played build.'
data = bytearray((base / 'AMOK.EXE').read_bytes())
pe = pefile.PE(data=data)
changes = []
def patch(address, old, new, reason):
    old, new = bytes.fromhex(old), bytes.fromhex(new)
    off = pe.get_offset_from_rva(address - 0x400000)
    assert len(old) == len(new) and data[off:off+len(old)] == old, hex(address)
    data[off:off+len(new)] = new
    changes.append(dict(address=hex(address), original=old.hex(), replacement=new.hex(), reason=reason))
def jump(src, dest):
    return b'\xe9' + struct.pack('<i', dest-src-5)
def install(address, code):
    off = pe.get_offset_from_rva(address-0x400000)
    assert not any(data[off:off+len(code)])
    patch(address, bytes(len(code)).hex(), code.hex(), 'Bounded polygon range helper')

for address in (0x415b11, 0x415d68):
    patch(address, '81fb00044200', '81fb00100801', 'Double remaining model/object drawing radius')
# Short compare requires a trampoline to retain instruction/branch boundaries.
at = 0xee0800
code = bytes.fromhex('81fa8c000000')
code += bytes.fromhex('0f8d') + struct.pack('<i', 0x4164d4-(at+12))
code += jump(at+12, 0x4164c3)
install(at, code)
patch(0x4164be, '83fa467d11', jump(0x4164be, at).hex(), 'Use 140-depth polygon terrain occlusion instead of 70')
patch(0x4164d4, '0518010000', '0530020000', 'Use final entry of expanded terrain occlusion column')
# Polygon sorting adds an eight-slot bias. Keep every model inside 148 heads.
at = 0xee0840
old = bytes.fromhex('8b8424a6000000c1f810894204')
code = old[:10] + bytes.fromhex('3d8c000000')
code += bytes.fromhex('0f8d') + struct.pack('<i', 0x4166d5-(at+21))
code += old[10:] + jump(at+24, 0x4164b0)
install(at, code)
patch(0x4164a3, old.hex(), (jump(0x4164a3, at)+bytes([0x90])*8).hex(), 'Guard expanded model depth before sorting and occlusion')
assert 139+8 < 148 and 140*4 == 0x230
# Decode helpers to verify exact branch targets and instruction boundaries.
md = Cs(CS_ARCH_X86, CS_MODE_32)
for address, expected_targets in ((0xee0800, [0x4164d4,0x4164c3]), (0xee0840,[0x4166d5,0x4164b0])):
    change = next(c for c in changes if int(c['address'],16)==address)
    ins = list(md.disasm(bytes.fromhex(change['replacement']),address))
    assert [int(i.op_str,16) for i in ins if i.mnemonic.startswith('j')] == expected_targets
shutil.copytree(base, target)
(target/'AMOK.EXE').write_bytes(data)
manifest = json.loads((target/'widescreen-patches.json').read_text(encoding='utf-8-sig')) + changes
(target/'widescreen-patches.json').write_text(json.dumps(manifest,indent=2))
for change in manifest:
    off = pe.get_offset_from_rva(int(change['address'],16)-0x400000)
    replacement = bytes.fromhex(change['replacement'])
    assert data[off:off+len(replacement)] == replacement
vpath=target/'validation.json'
v=json.loads(vpath.read_text(encoding='utf-8-sig'))
v.update(sha256=hashlib.sha256(data).hexdigest(), polygon_range_player_verified=False,
         polygon_occlusion_depth_limit=140, polygon_sort_depth_guard=140,
         remaining_object_squared_radius=0x1081000, polygon_patch_bytes_verified=True)
vpath.write_text(json.dumps(v,indent=2))
(target/'README.md').write_text('''# AMOK: polygon range correction test

Uses the confirmed smoother native 4K build, controls, cameras and subtle fog.
Two remaining object radius gates are doubled. Polygon terrain occlusion now
uses the expanded 140-depth range and final entry, with a sorting bounds guard.
The helper DLL and all game data are copied unchanged. Visual testing pending:
check enemy/model pop-in and the distant door from the reported mission.
''',encoding='utf-8')
source=Path('outputs/Amok-Enhancement-Source')
shutil.copy2(__file__,source/Path(__file__).name)
with (source/'BUILD-NOTES.md').open('a',encoding='utf-8') as f:
    f.write('\nPolygon range test: prepare_polygon_range.py copies the staged build. '
            'Remaining radius gates 0x415b11/0x415d68 double; 0x4164be/0x4164d4 '
            'use 140-depth occlusion and offset 560. A depth guard at 0x4164a3 '
            'retains the eight-head sorting bias within allocated storage. '
            'Patch bytes and helper branch targets verified; player test pending.\n')
print('Prepared polygon range test; all patch bytes and branch targets verified.')
