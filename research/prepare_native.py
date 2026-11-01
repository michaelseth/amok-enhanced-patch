from pathlib import Path
import struct, shutil, json, hashlib
source = Path(r'C:\Amok\AMOKFILS')
target = Path('outputs/Amok-Native').resolve()
target.mkdir(exist_ok=True)
for item in source.iterdir():
    if item.name == 'FILES95':
        continue
    if item.is_dir():
        shutil.copytree(item, target / item.name, dirs_exist_ok=True)
    else:
        shutil.copy2(item, target / item.name)
data = bytearray((source / 'FILES95/AMOK.BIN').read_bytes())
assert hashlib.sha256(data).hexdigest() == '09d505057e4fadf894100c332631137f7861de83c0f3606e067e7a55d3d0eb33'
pe = struct.unpack_from('<I', data, 0x3c)[0]
assert data[pe:pe+4] == b'PE\0\0'
count = struct.unpack_from('<H', data, pe+6)[0]
optional = struct.unpack_from('<H', data, pe+20)[0]
section_table = pe+24+optional
image_size = struct.unpack_from('<I', data, pe+24+56)[0]
boundaries = sorted([struct.unpack_from('<I', data, section_table+i*40+12)[0] for i in range(count)] + [image_size])
changes = []
for i in range(count):
    pos = section_table+i*40
    name = bytes(data[pos:pos+8]).rstrip(b'\0').decode()
    virtual, rva, raw, offset = struct.unpack_from('<IIII', data, pos+8)
    assert virtual == 0
    memory_size = boundaries[boundaries.index(rva)+1]-rva
    struct.pack_into('<I', data, pos+8, memory_size)
    changes.append({'section':name, 'virtual_size':memory_size, 'raw_size':raw})
(target / 'AMOK.EXE').write_bytes(data)
cd_init = 0x41ef94-0x410000+0x400
assert data[cd_init:cd_init+5] == bytes.fromhex('8d44243050')
data[cd_init:cd_init+5] = b'\xe9'+struct.pack('<i',0x41f080-(0x41ef94+5))
(target / 'AMOK.EXE').write_bytes(data)
(target / 'Start-Amok.cmd').write_text('@echo off\ncd /d "%~dp0"\nstart "" /wait "%~dp0AMOK.EXE"\n')
(target / 'header-repair.json').write_text(json.dumps(changes, indent=2))
print(target)
