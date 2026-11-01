from pathlib import Path
import shutil,struct,json,hashlib,sys

base=Path('outputs/Amok-2160p-4x3-Test')
target=Path('outputs/Amok-2160p-Widescreen-Fixed-Test')
if target.exists():
    assert '--finish-copy' in sys.argv, 'Do not overwrite a played test build or its settings.'
    assert (target/'AMOK.EXE').read_bytes()==(base/'AMOK.EXE').read_bytes()
else:
    shutil.copytree(base,target)
exe=target/'AMOK.EXE'
data=bytearray(exe.read_bytes())
def offset(va):
    return va-0x460000+0x41c00 if 0x460000<=va<0x460200 else va-0x410000+0x400
pos=offset(0x460106)
assert struct.unpack_from('<I',data,pos)[0]==2880
struct.pack_into('<I',data,pos,3840)
exe.write_bytes(data)
ini=target/'ddraw.ini'
ini.write_text(ini.read_text().replace('inject_resolution=2880x2160','inject_resolution=3840x2160'))
manifest=target/'widescreen-patches.json'
patches=json.loads(manifest.read_text())
for patch in patches:
    if patch['address']=='0x460100':
        patch['replacement']=data[offset(0x460100):offset(0x460100)+len(bytes.fromhex(patch['replacement']))].hex()
        patch['reason']='Request a 3840x2160 16-bit render surface'
manifest.write_text(json.dumps(patches,indent=2))
v=json.loads((target/'validation.json').read_text())
v.update(render_surface=[3840,2160],viewport=[3840,2160],original_horizontal_focal_scale=3072,
    terrain_reference_height=2400,terrain_alignment_player_verified=False,runtime_surface_verified=False,
    camera_behavior='Original horizontal field of view; reduced vertical view at 16:9',
    sha256=hashlib.sha256(data).hexdigest())
(target/'validation.json').write_text(json.dumps(v,indent=2))
(target/'README.md').write_text('''# AMOK: 4K widescreen terrain-fix test

Launch **Play-Amok-4K-Widescreen-Fixed.cmd** from the parent outputs folder.

This separate build renders at 3840×2160 with a full-height 16:9 viewport.
It carries the confirmed 4:3 build's terrain scale and bottom-up origin
corrections, expanded rendering buffers, and updated Xbox controller DLL.
The original horizontal field of view is retained. Relative to 4:3, this
shows less vertically; it does not reveal additional scenery at the sides.
The 4:3 build remains available through Play-Amok-4K-4x3.cmd.

Left stick moves and strafes; right stick turns. Left-stick click toggles
running; right-stick click cycles camera distance. RT/RB fires the minigun,
LT/X fires normal missiles, Y fires heavy missiles, A throws bombs/selects,
View/Back opens the map, and B goes back/skips. Start during a mission ends
the mission and returns to menus (Shift+Escape).

This widescreen build needs player confirmation of terrain/sprite alignment.
Menus and movies retain the original artwork proportions. The original game
files in C:/Amok are unchanged. A full playthrough has not been tested.
''')
print(target.resolve())
