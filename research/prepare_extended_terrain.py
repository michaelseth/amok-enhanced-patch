from pathlib import Path
import sys, shutil, struct, json, hashlib
sys.path.insert(0,str(Path(__file__).parent/'python-deps'))
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_OP_IMM

base=Path('outputs/Amok-2160p-No-Distance-Fog-Test')
target=Path('outputs/Amok-2160p-Extended-Terrain-Test')
assert not target.exists(), 'Do not overwrite a played build.'
source=(base/'AMOK.EXE').read_bytes()
pe=pefile.PE(data=source);data=bytearray(source);changes=[]
def patch(va,old,new,reason):
 off=pe.get_offset_from_rva(va-pe.OPTIONAL_HEADER.ImageBase)
 assert len(old)==len(new) and data[off:off+len(old)]==old
 data[off:off+len(new)]=new
 changes.append(dict(address=hex(va),original=old.hex(),replacement=new.hex(),reason=reason))
patch(0x42056a,bytes.fromhex('ba8c000000'),bytes.fromhex('ba18010000'),'Double optimized terrain renderer ray samples from 140 to 280')
# One framebuffer pointer plus one pointer per pair of terrain samples.
old_stride=4+140*2;new_stride=4+280*2
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
sites=[]
for section in pe.sections:
 if not section.Characteristics&0x20000000:continue
 for ins in md.disasm(section.get_data(),pe.OPTIONAL_HEADER.ImageBase+section.VirtualAddress):
  if not ins.id or not 0x411600<=ins.address<=0x422b20:continue
  if any(o.type==CS_OP_IMM and o.imm==old_stride for o in ins.operands):
   assert ins.imm_size==4
   replacement=bytearray(ins.bytes)
   struct.pack_into('<I',replacement,ins.imm_offset,new_stride)
   patch(ins.address,ins.bytes,replacement,'Expand sprite occlusion column stride for doubled terrain range')
   sites.append(hex(ins.address))
assert len(sites)>=10,sites
# Existing expanded tables have 4 MiB per region; leave all projection values unchanged.
assert new_stride*3840//2<0x400000
assert 280*3840*4//2<0x400000-0x2a50
shutil.copytree(base,target)
(target/'AMOK.EXE').write_bytes(data)
shutil.copy2('work/AMOKMOD-far.dll',target/'AMOKMOD.dll')
manifest=target/'widescreen-patches.json'
manifest.write_text(json.dumps(json.loads(manifest.read_text(encoding='utf-8-sig'))+changes,indent=2))
v=json.loads((target/'validation.json').read_text(encoding='utf-8-sig'))
v.update(sha256=hashlib.sha256(data).hexdigest(),runtime_surface_verified=False,
         terrain_range_samples=280,original_terrain_range_samples=140,
         terrain_range_player_verified=False,object_draw_distance_extended=False,
         terrain_sampler='Direct full-level terrain sample via renderer hook',
         expanded_occlusion_column_stride=new_stride,expanded_stride_sites=sites,
         controller_dll_matches_confirmed_build=False)
(target/'validation.json').write_text(json.dumps(v,indent=2))
(target/'README.md').write_text('''# AMOK: extended terrain distance experiment

Launch Play-Amok-4K-Extended-Terrain.cmd from the parent outputs folder.

The optimized terrain renderer takes 280 ray samples instead of 140. Beyond
the original cache it reads terrain directly from the level's terrain data.
Occlusion column storage is expanded. Near-camera projection is unchanged.
Distance fog is disabled to make the new terrain range visible.

This is a terrain-only experiment: object drawing limits are unchanged.
Terrain-range-status.txt records installation, near-cache sample comparisons,
and the first sample beyond the old range. Visual testing is pending.
Controls, HUD and camera correction are inherited from the confirmed build.
Play-Amok-4K-Widescreen-Fixed.cmd launches the confirmed version.
''',encoding='utf-8')
print('Extended terrain build created:',len(sites),'column stride sites expanded.')
