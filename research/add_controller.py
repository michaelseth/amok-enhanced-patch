from pathlib import Path
import sys,struct,shutil,json
sys.path.insert(0,str(Path(__file__).parent/'python-deps'))
import pefile
folder=Path(sys.argv[1]);filename=folder/'AMOK.EXE';data=bytearray(filename.read_bytes());p=pefile.PE(data=data)
entry=p.OPTIONAL_HEADER.ImageBase+p.OPTIONAL_HEADER.AddressOfEntryPoint
assert entry==0x44c826
stub=bytes.fromhex('9c606880014600ff15d8036b00a3c0014600ff15c0036b00a3c4014600619d')
stub+=b'\xe9'+struct.pack('<i',entry-(0x460140+len(stub)+5))
for address,code in [(0x460140,stub),(0x460180,b'AMOKMOD.dll\0')]:
 off=p.get_offset_from_rva(address-0x400000);assert not any(data[off:off+len(code)]);data[off:off+len(code)]=code
struct.pack_into('<I',data,p.OPTIONAL_HEADER.get_field_absolute_offset('AddressOfEntryPoint'),0x60140)
code_section=next(s for s in p.sections if s.VirtualAddress==0x60000)
struct.pack_into('<I',data,code_section.get_field_absolute_offset('Characteristics'),code_section.Characteristics|0x80000000)
# The EXE uses fixed absolute addresses throughout. Keep it at its preferred base
# and remove relocation support rather than retaining stale relocation records
# from rewritten instructions. The original image has no ASLR flag.
struct.pack_into('<H',data,p.FILE_HEADER.get_field_absolute_offset('Characteristics'),p.FILE_HEADER.Characteristics|1)
rel=p.OPTIONAL_HEADER.DATA_DIRECTORY[5]
struct.pack_into('<II',data,rel.get_file_offset(),0,0)
filename.write_bytes(data);shutil.copy2('work/AMOKMOD.dll',folder/'AMOKMOD.dll')
print('Added in-process XInput support:',folder)
