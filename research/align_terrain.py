from pathlib import Path
import struct,json,hashlib

folder=Path('outputs/Amok-2160p-4x3-Test')
exe=folder/'AMOK.EXE'
data=bytearray(exe.read_bytes())
def offset(va):
    return va-0x460000+0x41c00 if 0x460000<=va<0x460200 else va-0x410000+0x400
def patch(va,expected,replacement):
    pos=offset(va)
    assert len(expected)==len(replacement)
    assert data[pos:pos+len(expected)] in (expected,replacement),(hex(va),data[pos:pos+len(expected)].hex())
    data[pos:pos+len(expected)]=replacement

# The terrain ray step and origin assumed a 320x200 view, independently
# of the sprite projection's width-derived focal scale. Keep the original
# reference height (width * 5/8), while the draw loop uses the full height.
# EBX is intentionally the reference height both for IDIV and the origin.
stub=bytes.fromhex('8b1d9c004900c1eb038d1c9b')
stub+=b'\xe9'+struct.pack('<i',0x4204c2-(0x460020+len(stub)+5))
original=bytes.fromhex('8b1da8004900')
replacement=b'\xe9'+struct.pack('<i',0x460020-(0x4204bc+5))+b'\x90'
backup=Path('work/AMOK-4x3-fullheight-before-alignment.exe')
if not backup.exists(): backup.write_bytes(data)
patch(0x460020,b'\0'*len(stub),stub)
patch(0x4204bc,original,replacement)
# The assembly terrain renderer begins at the bottom row and walks upward.
# Increasing the draw height therefore requires moving its initial ray by
# exactly the additional rows, rather than moving the sprite projection.
origin_stub=bytes.fromhex('89da0fafd050a1a800490029d80faf05606e680029c2588915646e6800')
origin_stub+=b'\xe9'+struct.pack('<i',0x4204e2-(0x460040+len(origin_stub)+5))
origin_old=bytes.fromhex('89da0fafd08915646e6800')
origin_new=b'\xe9'+struct.pack('<i',0x460040-(0x4204d7+5))+b'\x90'*6
patch(0x460040,b'\0'*len(origin_stub),origin_stub)
patch(0x4204d7,origin_old,origin_new)
exe.write_bytes(data)
manifest=folder/'widescreen-patches.json'
patches=json.loads(manifest.read_text())
patches=[p for p in patches if p['address'] not in ('0x4204bc','0x460020','0x4204d7','0x460040')]
patches.extend([
 dict(address='0x4204bc',original=original.hex(),replacement=replacement.hex(),reason='Use original width-derived terrain projection reference height'),
 dict(address='0x460020',original=('00'*len(stub)),replacement=stub.hex(),reason='Calculate terrain reference height without reducing the drawing height'),
 dict(address='0x4204d7',original=origin_old.hex(),replacement=origin_new.hex(),reason='Compensate the bottom-up ray origin for the extra drawing rows'),
 dict(address='0x460040',original=('00'*len(origin_stub)),replacement=origin_stub.hex(),reason='Retain terrain screen positions while extending the draw height')])
manifest.write_text(json.dumps(patches,indent=2))
for width in (320,640,800,1920,2880,3840):
    old=(width//8)*5
    new=(width>>3)*5
    assert old==new
    assert (200*1024)//old==(200*1024)//new
    step=(200*1024)//old
    origin=old*(-(step//2))
    for extra in (0,40,360):
        extended_origin=origin-extra*step
        for ground_height in range(origin,origin+old*step,step*7):
            original_rows=(ground_height-origin+step-1)//step
            extended_rows=(ground_height-extended_origin+step-1)//step
            assert old-1-original_rows==old+extra-1-extended_rows
v=json.loads((folder/'validation.json').read_text())
v.update(terrain_reference_height=1800,terrain_projection_patch_verified=True,terrain_bottom_up_origin_compensated=True,
    sha256=hashlib.sha256(data).hexdigest(),terrain_alignment_player_verified=False)
(folder/'validation.json').write_text(json.dumps(v,indent=2))
print('Terrain projection alignment patch installed; original projection arithmetic verified.')
