from pathlib import Path
import sys,json,hashlib,ctypes as c,struct,shutil
sys.path.insert(0,str(Path(__file__).parent/'python-deps'))
import pefile
from capstone import *
records=[]
for height,width in [(1080,1920),(2160,3840)]:
 folder=Path(f'outputs/Amok-{height}p-Test');p=pefile.PE(str(folder/'AMOK.EXE'))
 assert p.FILE_HEADER.Machine==0x14c and p.OPTIONAL_HEADER.AddressOfEntryPoint==0x60140
 assert p.OPTIONAL_HEADER.SizeOfImage==0xae0000
 assert p.OPTIONAL_HEADER.DATA_DIRECTORY[5].Size==0
 assert any(s.Name.rstrip(b'\0')==b'.hdbuf' and s.Misc_VirtualSize==0x810000 for s in p.sections)
 changes=json.loads((folder/'expanded-render-tables.json').read_text());assert len(changes)==38
 md=Cs(CS_ARCH_X86,CS_MODE_32)
 for change in changes:
  address=int(change['instruction'],16);off=p.get_offset_from_rva(address-0x400000)
  instruction=next(md.disasm(p.__data__[off:off+15],address))
  assert change['new'] in instruction.op_str
 records.append({'resolution':[width,height],'exe_sha256':hashlib.sha256((folder/'AMOK.EXE').read_bytes()).hexdigest(),'relocated_references':len(changes),'structure_checks':'passed','controller_physical_input_confirmed':False,'full_playthrough_tested':False})
 shutil.copy2('outputs/AMOK-Controls-and-Status.md',folder/'README.md')
 (folder/'README.txt').write_text('Experimental native widescreen + XInput build. See README.md for controls, validation and remaining limitations. Use the launchers in the parent outputs folder to keep only one test running.\n')
k=c.WinDLL('kernel32');k.OpenProcess.restype=c.c_void_p;k.ReadProcessMemory.argtypes=[c.c_void_p,c.c_void_p,c.c_void_p,c.c_size_t,c.c_void_p];k.CloseHandle.argtypes=[c.c_void_p]
handle=k.OpenProcess(0x10,False,int(sys.argv[1]));assert handle
def read(addr,count):
 buf=c.create_string_buffer(count*4);assert k.ReadProcessMemory(handle,addr,buf,len(buf),None)
 return struct.unpack('<'+'I'*count,buf.raw)
display=read(0x6835f4,8);view=read(0x490080,24)
assert display[4:7]==(3840,2160,16)
assert view[7]==3840 and view[10]==1800 and view[13]==7680
assert 0x6d0000<=view[21]<0xad0000
records[1]['runtime']={'display':list(display),'view':list(view),'render_surface_verified':True,'3d_scene_visually_observed':True,'menu_layout_confirmed':False}
k.CloseHandle(handle)
Path('outputs/hd-validation.json').write_text(json.dumps(records,indent=2));print('HD executable structures, 38 relocated references per build and live 4K surface verified.')
