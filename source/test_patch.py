from pathlib import Path
import hashlib, json, shutil, subprocess, sys, uuid, zipfile

root = Path(__file__).resolve().parents[2]
package = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else root / 'outputs/Amok-Enhanced-Patch-0.1.0-preview'
test = root / 'work' / ('Patch Verification ' + uuid.uuid4().hex[:8])
test.mkdir()
assert test.resolve().is_relative_to((root / 'work').resolve())
original_root = Path('C:/Amok')
manifest = json.loads((package / 'patch-manifest.json').read_text())
results = []
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def run(name, source, destination, pkg=package, success=False):
    command = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
               '-File', str(pkg / 'Apply-Patch.ps1'), '-NoGui',
               '-Source', str(source), '-Destination', str(destination)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=90)
    assert (result.returncode == 0) == success, (name, result.stdout, result.stderr)
    if not success and name != 'existing destination':
        assert not destination.exists(), (name, 'Unexpected output')
    results.append({'test': name, 'passed': True, 'output': result.stdout.strip()})

before = {a['path']: sha(original_root / 'AMOKFILS' / a['path']) for a in manifest['assets']}
before_exe = sha(original_root / 'AMOKFILS/FILES95/AMOK.BIN')
good = test / 'Enhanced Game'
run('CD root and paths with spaces', original_root, good, success=True)
assert sha(good / 'Game/AMOK.EXE') == manifest['result_sha256']
for a in manifest['assets']:
    assert sha(good / 'Game' / a['path']) == a['sha256']
for f in manifest['payload']:
    assert sha(good / f['path']) == f['sha256']
run('AMOKFILS folder', original_root / 'AMOKFILS', test / 'From Data Folder', success=True)
run('FILES95 folder', original_root / 'AMOKFILS/FILES95', test / 'From Exe Folder', success=True)
run('existing destination', original_root, good)
assert sha(good / 'Game/AMOK.EXE') == manifest['result_sha256']
incomplete = test / 'Incomplete Game'
(incomplete / 'FILES95').mkdir(parents=True)
shutil.copy2(original_root / 'AMOKFILS/FILES95/AMOK.BIN', incomplete / 'FILES95/AMOK.BIN')
run('missing game data', incomplete, test / 'Must Not Exist 1')
wrong = test / 'Wrong Edition'
wrong.mkdir()
(wrong / 'AMOK.EXE').write_bytes(b'unsupported executable')
run('unsupported executable', wrong, test / 'Must Not Exist 2')
installed = test / 'Installed Original'
shutil.copytree(original_root / 'AMOKFILS', installed)
shutil.copy2(installed / 'FILES95/AMOK.BIN', installed / 'AMOK.EXE')
# An installed game does not need the CD's FILES95 directory.
# Rename rather than delete so the test preserves every source file.
(installed / 'FILES95').rename(test / 'Unused CD Setup')
run('installed original AMOK.EXE', installed, test / 'From Installed Game', success=True)
asset_path = installed / manifest['assets'][0]['path']
asset_path.write_bytes(asset_path.read_bytes() + b'changed')
run('modified game data', installed, test / 'Must Not Exist 3')
damaged = test / 'Damaged Patch'
shutil.copytree(package, damaged)
(damaged / 'payload/Game/ddraw.ini').write_text('damaged')
run('damaged helper/config', original_root, test / 'Must Not Exist 4', pkg=damaged)
bad_delta = test / 'Damaged Delta'
shutil.copytree(package, bad_delta)
bad_manifest = json.loads((bad_delta / 'patch-manifest.json').read_text())
bad_manifest['changes'][0]['bytes'] = 'AAAA'
(bad_delta / 'patch-manifest.json').write_text(json.dumps(bad_manifest))
run('damaged executable patch', original_root, test / 'Must Not Exist 5', pkg=bad_delta)
for a in manifest['assets']:
    assert sha(original_root / 'AMOKFILS' / a['path']) == before[a['path']]
assert sha(original_root / 'AMOKFILS/FILES95/AMOK.BIN') == before_exe
with zipfile.ZipFile(package.parent / (package.name + '.zip')) as z:
    assert z.testzip() is None
    # No complete game executable or original asset is allowed in the release.
    forbidden = {a['path'].lower() for a in manifest['assets']} | {'amok.exe', 'amok.bin', 'amokdos.bin'}
    for name in z.namelist():
        relative = '/'.join(name.split('/')[1:]).lower()
        assert relative not in forbidden and Path(relative).name not in {Path(n).name for n in forbidden}
report = {'checks': results, 'original_unchanged': True,
          'generated_executable_matches_confirmed_build': True,
          'archive_integrity': 'passed', 'no_game_executable_or_assets_in_release': True,
          'launch_test_folder': str(good), 'separate_clean_pc_tested': False}
(root / 'outputs/Amok-Patch-Verification.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
