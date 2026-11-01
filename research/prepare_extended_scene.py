from pathlib import Path
import sys,shutil,struct,json,hashlib
sys.path.insert(0,str(Path(__file__).parent/'python-deps'))
import pefile
from capstone import *
base=Path('outputs/Amok-2160p-Extended-Terrain-Test')
target=Path('outputs/Amok-2160p-Extended-Scene-Test')
assert not target.exists(), 'Do not overwrite a played build.'
source=(base/'AMOK.EXE').read_bytes();data=bytearray(source);pe=pefile.PE(data=source)
new_rva=pe.OPTIONAL_HEADER.SizeOfImage;va=0x400000+new_rva
payload=bytearray(0x3000);code_pos=0;changes=[]
heads=va+0x1000;palettes=va+0x2000;pool=va+0x4000;temp=va+0x1300
for row,address in enumerate((0x4fa698,0x4fd6b8,0x4fe6b8)):
 struct.pack_into('<148I',payload,0x2000+row*148*4,*([address]*148))
def patch(address,old,new,reason):
 off=pe.get_offset_from_rva(address-0x400000)
 assert len(old)==len(new) and data[off:off+len(old)]==old,(hex(address),data[off:off+len(old)].hex(),old.hex())
 data[off:off+len(new)]=new
 changes.append(dict(address=hex(address),original=old.hex(),replacement=new.hex(),reason=reason))
def stub(code):
 global code_pos
 address=va+code_pos;payload[code_pos:code_pos+len(code)]=code;code_pos=(code_pos+len(code)+15)&~15
 assert code_pos<0x1000
 return address
def jump(src,dst):return b'\xe9'+struct.pack('<i',dst-(src+5))
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
# Expand short signed-immediate comparisons without disturbing branch targets.
def compare_branch(address,newlimit):
 off=pe.get_offset_from_rva(address-0x400000)
 ins=list(md.disasm(source[off:off+16],address))[:2]
 cmp,branch=ins
 assert cmp.mnemonic=='cmp' and cmp.bytes[0]==0x83 and branch.mnemonic.startswith('j')
 length=cmp.size+branch.size;dest=branch.operands[0].imm
 condition=(branch.bytes[0]&15) if branch.size==2 else branch.bytes[1]&15
 at=va+code_pos
 code=b'\x81'+bytes([cmp.bytes[1]])+struct.pack('<i',newlimit)
 code+=bytes([0x0f,0x80|condition])+struct.pack('<i',dest-(at+12))
 code+=jump(at+12,address+length)
 target_stub=stub(code)
 patch(address,source[off:off+length],jump(address,target_stub)+b'\x90'*(length-5),'Expand distance comparison while retaining its original branch')

# Four offset calculations used arithmetic for 71*4 instead of an immediate 284.
old=bytes.fromhex('c1e00301e8c1e00329e8')
patch(0x420beb,old,bytes.fromhex('69c08d000000')+b'\x90'*4,'Expand computed occlusion column offset to 141*4')
old=bytes.fromhex('8d04d50000000001d0c1e00329d0')
for address in (0x420ec4,0x421118,0x4215a4):
 patch(address,old,bytes.fromhex('69c28d000000')+b'\x90'*8,'Expand computed occlusion column offset to 141*4')
# The first expression uses EAX==EBP at entry; all preserve the source registers.
for column in range(1920):assert column*141*4==column*564
for address in (0x413b5f,0x413b9f,0x420bbf,0x420d64):compare_branch(address,148)
for address in (0x420c07,0x420ee3):compare_branch(address,140)
patch(0x420c16,bytes.fromhex('0518010000'),bytes.fromhex('0530020000'),'Use extended final terrain occlusion entry')
patch(0x420ef2,bytes.fromhex('81c518010000'),bytes.fromhex('81c530020000'),'Use extended final terrain occlusion entry')
# Relocate sorting heads, clear-distance palettes, object pool, and chunk descriptors.
remap={0x49105c:heads,0x49107c:heads+32,0x4900fc:temp,
       0x4fa2c8:palettes+148*4,0x4fa420:palettes+148*8}
for section in pe.sections:
 if not section.Characteristics&0x20000000:continue
 for ins in md.disasm(section.get_data(),0x400000+section.VirtualAddress):
  if not ins.id:continue
  for operand in ins.operands:
   value=operand.imm if operand.type==CS_OP_IMM else operand.mem.disp if operand.type==CS_OP_MEM else 0
   # Keep original palette generation confined to original tables.
   dest=remap.get(value) if not (0x411d00<=ins.address<0x412100 and value in (0x4fa2c8,0x4fa420)) else None
   if 0x4ef4f0<=value<0x4f2af0:dest=pool+value-0x4ef4f0
   if dest is None:continue
   offset=ins.imm_offset if operand.type==CS_OP_IMM else ins.disp_offset
   size=ins.imm_size if operand.type==CS_OP_IMM else ins.disp_size
   assert size==4
   patch(ins.address+offset,struct.pack('<I',value),struct.pack('<I',dest),'Relocate expanded sprite storage')
patch(0x4127dc,bytes.fromhex('ba60000000'),bytes.fromhex('ba00020000'),'Expand scenery object pool from 96 to 512 slots')
compare_branch(0x41283f,512)
# Gather a centered 5x5 chunk area rather than 3x3, with independent descriptor storage.
at=va+code_pos
code=bytes.fromhex('83ea0283e8026689542418')
code+=jump(at+len(code),0x413c17)
address=stub(code)
patch(0x413c10,bytes.fromhex('4a486689542418'),jump(0x413c10,address)+b'\x90'*2,'Center enlarged scenery chunk gathering area')
patch(0x413c95,bytes.fromhex('81e800060000'),bytes.fromhex('81e8000a0000'),'Advance across five scenery chunks per row')
patch(0x413c80,bytes.fromhex('83c734'),bytes.fromhex('83c72c'),'Retain 16-chunk map row stride after scanning five columns')
patch(0x413c83,bytes.fromhex('83c334'),bytes.fromhex('83c32c'),'Retain matching scenery data row stride after scanning five columns')
patch(0x413cac,bytes.fromhex('83f803'),bytes.fromhex('83f805'),'Gather five scenery chunk rows')
patch(0x413d3a,bytes.fromhex('83f803'),bytes.fromhex('83f805'),'Gather five scenery chunk columns')
patch(0x415675,bytes.fromhex('83f809'),bytes.fromhex('83f819'),'Project all 25 gathered scenery chunks')
patch(0x413eb8,bytes.fromhex('81fa69540000'),bytes.fromhex('81faa4510100'),'Double scenery activation radius from 147 to 294 world units')
# A separate distance gate excludes some active world objects before projection.
patch(0x425eb8,bytes.fromhex('817db400640000'),bytes.fromhex('817db400900100'),'Double object visibility radius from 100 to 200 world units')
header=pe.sections[-1].get_file_offset()+40
assert header+40<=pe.OPTIONAL_HEADER.SizeOfHeaders and not any(data[header:header+40])
raw=(len(data)+0x1ff)&~0x1ff
data.extend(b'\0'*(raw-len(data)));data.extend(payload)
data[header:header+40]=struct.pack('<8sIIIIIIHHI',b'.farfix\0',0x20000,new_rva,len(payload),raw,0,0,0,0,0xe0000040)
struct.pack_into('<H',data,pe.FILE_HEADER.get_field_absolute_offset('NumberOfSections'),pe.FILE_HEADER.NumberOfSections+1)
struct.pack_into('<I',data,pe.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfImage'),new_rva+0x20000)
assert pool+512*144<=va+0x20000 and temp+25*20<heads+0x1000
shutil.copytree(base,target)
(target/'AMOK.EXE').write_bytes(data)
manifest=target/'widescreen-patches.json'
manifest.write_text(json.dumps(json.loads(manifest.read_text(encoding='utf-8-sig'))+changes,indent=2))
v=json.loads((target/'validation.json').read_text(encoding='utf-8-sig'))
v.update(sha256=hashlib.sha256(data).hexdigest(),runtime_surface_verified=False,
 sprite_flicker_fix_player_verified=False,extended_scene_player_verified=False,
 sprite_depth_limit=148,original_sprite_depth_limit=78,scenery_pool_slots=512,
 scenery_chunk_area=[5,5],object_draw_distance_extended=True,hard_draw_distance_extended=True,
 terrain_range_player_verified=True,terrain_only_player_report='Terrain farther; sprites flickered and remained limited in distance')
(target/'validation.json').write_text(json.dumps(v,indent=2))
(target/'README.md').write_text('''# AMOK: extended terrain and sprite range experiment

Launch Play-Amok-4K-Extended-Scene.cmd from the parent outputs folder.

Extends the terrain range from 140 to 280 samples and the matching sprite
depth limit from 78 to 148. Four computed occlusion offsets now use the
expanded column width. Sorting and palette tables are expanded separately.
Scenery gathers a 5x5 chunk area using 512 slots instead of 3x3 and 96 slots.
Distance fog is disabled for comparison. Visual testing is pending.

This experiment may cost more CPU time and activate scenery objects farther
away. Controls, HUD, camera overlay and near projection are retained.
The confirmed original-range widescreen version remains available through
Play-Amok-4K-Widescreen-Fixed.cmd.
''',encoding='utf-8')
print('Created extended scene build:',len(changes),'patches, new storage at',hex(va))
