import sys,struct,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'python-deps'))
import pefile
from capstone import *
folder=Path(sys.argv[1]);filename=folder/'AMOK.EXE';data=bytearray(filename.read_bytes());p=pefile.PE(data=data)
# Separate storage for the sprite column and silhouette tables. Original
# allocations contain 128 columns (284 bytes each) and 264 silhouette rows.
# 2160p focal scale can require 288 columns and 549 silhouette rows.
new_rva=p.OPTIONAL_HEADER.SizeOfImage;new_base=0x400000+new_rva
regions=[(0x4911b4,0x4c0694,new_base,0x400000),(0x4c0694,0x4c94b2,new_base+0x400000,0x400000),(0x4c94b2,0x4c98d4,new_base+0x800000,0x10000)]
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
patches=[]
for s in p.sections:
 if not s.Characteristics&0x20000000:continue
 for i in md.disasm(s.get_data(),0x400000+s.VirtualAddress):
  if i.id==0:continue
  for operand in i.operands:
   value=operand.imm if operand.type==CS_OP_IMM else operand.mem.disp if operand.type==CS_OP_MEM else 0
   for lo,hi,dest,size in regions:
    if lo<=value<hi:
     shift=i.imm_offset if operand.type==CS_OP_IMM else i.disp_offset
     length=i.imm_size if operand.type==CS_OP_IMM else i.disp_size
     assert length==4
     off=p.get_offset_from_rva(i.address-0x400000)+shift
     struct.pack_into('<I',data,off,dest+value-lo)
     patches.append({'instruction':hex(i.address),'old':hex(value),'new':hex(dest+value-lo)})
header=p.sections[-1].get_file_offset()+40
assert header+40<=p.OPTIONAL_HEADER.SizeOfHeaders and not any(data[header:header+40])
data[header:header+40]=struct.pack('<8sIIIIIIHHI',b'.hdbuf\0\0',0x810000,new_rva,0,0,0,0,0,0,0xc0000080)
struct.pack_into('<H',data,p.FILE_HEADER.get_field_absolute_offset('NumberOfSections'),p.FILE_HEADER.NumberOfSections+1)
struct.pack_into('<I',data,p.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfImage'),new_rva+0x810000)
filename.write_bytes(data);(folder/'expanded-render-tables.json').write_text(json.dumps(patches,indent=2))
print('Relocated render tables:',len(patches),'references')
