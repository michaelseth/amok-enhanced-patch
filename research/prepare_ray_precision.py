from pathlib import Path
import shutil,json,hashlib
base=Path('outputs/Amok-2160p-Polygon-Range-Test')
target=Path('outputs/Amok-2160p-Ray-Precision-Test')
assert not target.exists(), 'Do not overwrite a played build.'
shutil.copytree(base,target)
shutil.copy2('work/AMOKMOD-ray-precision.dll',target/'AMOKMOD.dll')
vpath=target/'validation.json'
v=json.loads(vpath.read_text(encoding='utf-8-sig'))
v.update(ray_precision_player_verified=False, ray_precision_arithmetic_cases_verified=125827200,
 helper_sha256=hashlib.sha256((target/'AMOKMOD.dll').read_bytes()).hexdigest())
vpath.write_text(json.dumps(v,indent=2))
(target/'README.md').write_text('''# AMOK: terrain ray precision comparison

Based on the player-confirmed enemy/door correction, with native 4K,
extended range, subtle fog, controller and HUD/camera fixes retained.
Carries the horizontal ray-spacing division remainder across columns,
avoiding accumulated truncation error as the camera changes direction.
125,827,200 synthetic signed ray positions match exact division.
The native-versus-staged first-frame comparison remains enabled.
Visual comparison and full playthrough are pending.
''',encoding='utf-8')
source=Path('outputs/Amok-Enhancement-Source')
for name in ('amok_fast_terrain.c','amok_ray_precision.c','test_ray_precision.c','prepare_ray_precision.py'):
 shutil.copy2(Path('work')/name,source/name)
with (source/'BUILD-NOTES.md').open('a',encoding='utf-8') as f:
 f.write('\nRay precision experiment: add -DAMOK_RAY_PRECISION to staged helper flags. '
         'Hook 0x6a059e distributes signed horizontal ray-spacing division remainders. '
         'Recovered numerators must match stock setup; unsupported modes retain original adds. '
         '125,827,200 signed ray positions match exact division. Player comparison pending.\n')
print('Prepared separate terrain ray precision comparison.')
