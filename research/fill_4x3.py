from pathlib import Path
import json

folder=Path('outputs/Amok-2160p-4x3-Test')
exe=folder/'AMOK.EXE'
data=bytearray(exe.read_bytes())
pos=0x424861-0x410000+0x400
original=bytes.fromhex('89d8c1e2031bc2c1f80389c2c1e00201d089dabe40010000c1e208a3a800490089d0c1fa1ff7fe')
# Full client height, preserving the stock focal scale derived from width.
replacement=bytes.fromhex('89c8a3a800490089d8c1e00899be40010000f7fe')
replacement+=b'\x90'*(len(original)-len(replacement))
assert data[pos:pos+len(original)] in (original,replacement)
backup=Path('work/AMOK-4x3-letterboxed.exe')
if not backup.exists(): backup.write_bytes(data)
data[pos:pos+len(original)]=replacement
exe.write_bytes(data)
manifest=folder/'widescreen-patches.json'
patches=json.loads(manifest.read_text())
patches=[p for p in patches if p['address']!='0x424861']
patches.append(dict(address='0x424861',original=original.hex(),replacement=replacement.hex(),reason='Fill the 4:3 viewport vertically; preserve original horizontal focal scale'))
manifest.write_text(json.dumps(patches,indent=2))
print('Full-height 4:3 viewport installed.')
