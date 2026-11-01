"""Build a sparse replacement patch; no complete game executable or assets are distributed."""
from pathlib import Path
import argparse, base64, hashlib, json, shutil, zipfile

def digest(data):
    return hashlib.sha256(data).hexdigest()

def build(original_path, game, portable, output):
    archive = output.parent / (output.name + '.zip')
    original = original_path.read_bytes()
    assert digest(original) == '09d505057e4fadf894100c332631137f7861de83c0f3606e067e7a55d3d0eb33'
    result = (game / 'AMOK.EXE').read_bytes()
    assert len(result) >= len(original)
    assert not output.exists() and not archive.exists(), 'Refusing to overwrite an existing release'
    output.mkdir(parents=True)
    changes = []
    pos = 0
    while pos < len(result):
        if pos < len(original) and result[pos] == original[pos]:
            pos += 1
            continue
        start = pos
        while pos < len(result) and (pos >= len(original) or result[pos] != original[pos]):
            pos += 1
        changes.append({'offset': start, 'bytes': base64.b64encode(result[start:pos]).decode('ascii')})
    rebuilt = bytearray(original) + bytearray(len(result) - len(original))
    for change in changes:
        data = base64.b64decode(change['bytes'])
        rebuilt[change['offset']:change['offset'] + len(data)] = data
    assert rebuilt == result
    assets = []
    payload = []
    helpers = {'AMOKMOD.dll', 'ddraw.dll', 'ddraw.ini', 'cnc-ddraw-LICENSE.txt'}
    for p in sorted((portable / 'Game').rglob('*')):
        if not p.is_file() or p.name == 'AMOK.EXE':
            continue
        relative = p.relative_to(portable / 'Game').as_posix()
        if p.name in helpers:
            target = output / 'payload/Game' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
            payload.append({'path': 'Game/' + relative, 'sha256': digest(p.read_bytes())})
        else:
            assets.append({'path': relative, 'sha256': digest(p.read_bytes())})
    for name in ['Play-Amok.cmd', 'README.txt']:
        target = output / 'payload' / name
        shutil.copy2(portable / name, target)
        if name == 'README.txt':
            guide = target.read_text(encoding='utf-8')
            start = guide.index('GETTING STARTED')
            end = guide.index('\nDISPLAY')
            guide = guide[:start] + '''GETTING STARTED
Double-click Play-Amok.cmd to play.
Keep the Game folder beside Play-Amok.cmd. Move this whole folder together
when copying it to another Windows 10/11 PC. No installation is needed.
Use a writable folder. Your original game files were copied, not modified.
''' + guide[end:]
            target.write_text(guide, encoding='utf-8')
        payload.append({'path': name, 'sha256': digest(target.read_bytes())})
    # The generated game's guide describes the result, while release instructions
    # describe applying the patch. No game files are embedded in the source bundle.
    manifest = {'format': 1, 'version': '0.1.0-preview',
                'original_sha256': digest(original), 'result_sha256': digest(result),
                'original_size': len(original), 'result_size': len(result),
                'changes': changes, 'assets': assets, 'payload': payload}
    (output / 'patch-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    here = Path(__file__).parent
    for name in ['Apply-Patch.ps1', 'Apply-Amok-Patch.cmd', 'README.txt']:
        shutil.copy2(here / name, output / name)
    source_dir = output / 'Source'
    source_dir.mkdir()
    for p in here.iterdir():
        if p.is_file():
            shutil.copy2(p, source_dir / p.name)
    work = here.parent
    for name in ['amok_xinput.c', 'amok_far_terrain.c', 'amok_fast_terrain.c',
                 'amok_terrain_staging.c', 'amok_ray_precision.c']:
        helper_source = here / name if (here / name).exists() else work / name
        shutil.copy2(helper_source, source_dir / name)
    (output / 'SHA256SUMS.txt').write_text(''.join(
        digest(p.read_bytes()) + '  ' + p.relative_to(output).as_posix() + '\n'
        for p in sorted(output.rglob('*')) if p.is_file()), encoding='ascii')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(output.rglob('*')):
            if p.is_file():
                z.write(p, (Path(output.name) / p.relative_to(output)).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
    print(json.dumps({'directory': str(output), 'archive_bytes': archive.stat().st_size,
                      'replacement_ranges': len(changes),
                      'replacement_bytes': sum(len(base64.b64decode(c['bytes'])) for c in changes),
                      'player_supplied_files': len(assets), 'result_sha256': digest(result)}, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--portable', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.original, args.game, args.portable, args.output)
