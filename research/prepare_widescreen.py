from pathlib import Path
import shutil, struct, json, hashlib, sys
width=int(sys.argv[1]) if len(sys.argv)>1 else 800
height=int(sys.argv[2]) if len(sys.argv)>2 else 450
original_camera='--original-camera' in sys.argv
base=Path('outputs/Amok-Native').resolve()
target=Path(f'outputs/Amok-{height}p-4x3-Test' if original_camera else 'outputs/Amok-Widescreen-Prototype' if width==800 else f'outputs/Amok-{height}p-Test').resolve()
shutil.copytree(base,target,dirs_exist_ok=True)
data=bytearray((base/'AMOK.EXE').read_bytes())
patches=[]
def offset(address):
    if 0x460000 <= address < 0x460200:
        return address-0x460000+0x41c00
    return address-0x410000+0x400
def patch(address, expected, replacement, reason):
    pos=offset(address)
    assert data[pos:pos+len(expected)]==expected,(hex(address),data[pos:pos+len(expected)].hex())
    assert len(expected)==len(replacement)
    data[pos:pos+len(expected)]=replacement
    patches.append({'address':hex(address),'original':expected.hex(),'replacement':replacement.hex(),'reason':reason})
patch(0x424a26,bytes.fromhex('68c8000000'),b'\x68'+struct.pack('<I',360),'Initial client height 360')
patch(0x424a82,bytes.fromhex('b940010000'),b'\xb9'+struct.pack('<I',640),'Initial client width 640')
stub=b'\xb8\x01\x00\x00\x00\xba'+struct.pack('<I',width)+b'\xbb'+struct.pack('<I',height)+bytes.fromhex('b91000000089d5899c2484000000')
stub+=b'\xe9'+struct.pack('<i',0x41cd5c-(0x460100+len(stub)+5))
patch(0x460100,b'\x00'*len(stub),stub,f'Request a {width}x{height} 16-bit render surface')
patch(0x41cd53,bytes.fromhex('89d5899c2484000000'),b'\xe9'+struct.pack('<i',0x460100-(0x41cd53+5))+b'\x90'*4,'Route display initialization through the widescreen dimensions')
patch(0x424afa,bytes.fromhex('8b44240c'),bytes.fromhex('31c09090'),'Disable initial interlaced TV rendering')
patch(0x423411,bytes.fromhex('8b158c004900'),bytes.fromhex('ba4001000090'),'Keep 320x200 intro and menu images centered without exceeding the render surface')
if width>=1920:
    # Preserve AX (the pixel format), and choose the smaller of the client
    # width and height * 320/200 before the original integer-scale calculation.
    menu_stub=bytes.fromhex('5051a1900049006bc00899b905000000f7f93b058c0049007e05a18c00490089c25958')
    menu_stub+=b'\xe9'+struct.pack('<i',0x423417-(0x4601d0+len(menu_stub)+5))
    patch(0x4601d0,b'\x00'*len(menu_stub),menu_stub,'Choose a menu image scale that fits both client dimensions')
    pos=offset(0x423411)
    data[pos:pos+6]=b'\xe9'+struct.pack('<i',0x4601d0-(0x423411+5))+b'\x90'
    menu_patch=next(p for p in patches if p['address']=='0x423411')
    menu_patch['replacement']=data[pos:pos+6].hex()
    menu_patch['reason']='Use the fitted integer-scale menu image routine'
original=data[offset(0x424861):offset(0x424888)]
assert original.hex()=='89d8c1e2031bc2c1f80389c2c1e00201d089dabe40010000c1e208a3a800490089d0c1fa1ff7fe'
# View height = client height * 5 / 6. Focal scale = view height * 256 / 200.
# Preserves the original 320x240 framing while widening the view at 16:9.
replacement=bytes.fromhex('89c86bc00599be06000000f7fea3a8004900c1e00899bec8000000f7fe')
# Retain the original width and focal-scale stores immediately after this span.
span=data[offset(0x424861):offset(0x424888)]
replacement+=b'\x90'*(len(span)-len(replacement))
if not original_camera:
    patch(0x424861,span,replacement,'Derive viewport height and projection scale from client height')
(target/'AMOK.EXE').write_bytes(data)
(target/'widescreen-patches.json').write_text(json.dumps(patches,indent=2))
(target/'ddraw.ini').write_text(f'[ddraw]\nwindowed=true\nfullscreen=true\nwidth=0\nheight=0\nmaintas=true\nrenderer=auto\ndevmode=true\nsavesettings=0\nmaxfps=60\nmaxgameticks=60\nresizable=true\ninject_resolution={width}x{height}\nborder=false\ntoggle_borderless=true\nfixchilds=0\nhook=4\n')
print(target)
print('SHA256',hashlib.sha256(data).hexdigest())
