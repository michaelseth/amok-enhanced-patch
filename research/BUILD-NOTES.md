# Build notes

Run the Python scripts from the original task workspace. They require
`pefile` and `capstone` installed under `work/python-deps`, and the original
game at `C:/Amok`. First run `prepare_native.py` to create the compatibility
baseline, then build the 32-bit controller DLL:

```powershell
clang --target=i686-w64-mingw32 -shared -O2 -DAMOK_MOD work/amok_xinput.c -o work/AMOKMOD.dll -luser32
clang -O2 work/amok_xinput.c -o work/controller-tests.exe -luser32
./work/controller-tests.exe
```

For each target, with that target's game process closed, run:

```powershell
python work/prepare_widescreen.py 1920 1080
python work/add_controller.py outputs/Amok-1080p-Test
python work/expand_render_tables.py outputs/Amok-1080p-Test
python work/prepare_widescreen.py 3840 2160
python work/add_controller.py outputs/Amok-2160p-Test
python work/expand_render_tables.py outputs/Amok-2160p-Test
python work/prepare_widescreen.py 2880 2160 --original-camera
python work/add_controller.py outputs/Amok-2160p-4x3-Test
python work/expand_render_tables.py outputs/Amok-2160p-4x3-Test
python work/fill_4x3.py
python work/align_terrain.py
python work/prepare_fixed_widescreen.py
```

The 32-bit Windows compiler must provide Windows/XInput headers and import
libraries. This task used the already installed LLVM/MinGW toolchain.
The scripts in this folder are copies of the work sources; copy them into
`work/` before running the commands above. The baseline includes cnc-ddraw
and its supplied license. `validate_hd.py <running-4K-process-ID>` validates
both executables and reads the live 4K display state. It does not automate
or confirm a complete playthrough or physical controller testing.

The full-height 4:3 patch preserves the original width-derived focal scale
but replaces the width-derived letterboxed viewport height with the client
height. The terrain alignment patch separately retains width*5/8 as its
ray projection reference height, matching the stock sprite projection.
The assembly terrain renderer draws upward from the bottom of the image;
the starting ray is decreased by (draw_height-reference_height)*ray_step.
prepare_fixed_widescreen.py copies the confirmed 4:3 build into a new
3840x2160 test folder. It retains the original horizontal field of view;
the 16:9 image has a reduced vertical view. It preserves the source build's
files and refuses to overwrite an existing widescreen test folder by default.
The extra rows extend the scene below the original viewport; the original
camera center is retained. The current controller
source uses gameplay state 1 for independent Z/X strafing and a run toggle,
R3 for F1 camera distance, and Start for Shift+Escape to end a mission.
Earlier widescreen output folders still contain their previous controller
DLL; rebuild them explicitly to apply the new controls there too.
Recreating a target copies baseline game data and can replace its settings;
back up saves and settings before running preparation scripts again.

Camera overlay patch: run work/fix_camera_overlay.py against the existing fixed widescreen build. The shared compass/waypoint Y row receives a camera-profile correction (0, -216, -584 pixels at 3840x2160). The main ammo/health/radar scale is restored to 2304 while world projection stays at 3072. Player verification of alternate-camera alignment is pending.

Player subsequently confirmed alternate-camera compass/waypoint alignment and the smaller main HUD in the widescreen build.

Later-fog comparison: run work/prepare_later_fog.py once to copy the confirmed widescreen build to Amok-2160p-Later-Fog-Test and delay terrain/object fog onset. Original hard drawing limits are retained. All five fade profiles and palette lookup bounds were checked; player testing is pending.

No-distance-fog comparison: work/prepare_no_distance_fog.py copies the confirmed widescreen build and zeroes the terrain/object palette fade step at 0x411f5b and 0x41200a. Existing denominators, palette tables, draw limits and lighting remain intact. Visual testing is pending.

Extended-terrain experiment: compile amok_xinput.c for i686 with -shared -O2 -mstackrealign -DAMOK_MOD -DAMOK_FAR_TERRAIN and -luser32, output work/AMOKMOD-far.dll, then run work/prepare_extended_terrain.py once. This doubles optimized terrain ray samples from 140 to 280, expands 13 occlusion column stride sites from 284 to 564, and hooks the two terrain sample sites to read the level terrain data. Runtime hook installation verified. Controller mapping checks passed. Object drawing limits remain unchanged; near-cache parity and player visual confirmation are pending.

Extended renderer mission runtime: 3840x2160 surface verified; 10,000 nearby samples exactly matched the game's original terrain cache; direct sampling beyond the old terrain range was observed.

Extended-scene correction: work/prepare_extended_scene.py adds .farfix storage and comparison stubs, corrects four computed column offsets missed by the terrain-only patch, extends sprite depth/sorting/palette ranges, expands the scenery pool to 512 slots, and gathers 5x5 scenery chunks in relocated descriptors. Mission verification is pending.

Extended-scene runtime: 280 terrain samples confirmed; scenery free/active nodes use relocated 512-slot storage. All 35 additional scene patch byte sequences and the new PE storage section were verified.

Scenery visibility regression: enlarged 5x5 scan retained the original
three-column row remainder (52 bytes), skipping two chunks per row.
Corrected 0x413c80 and 0x413c83 to 44 bytes: 5*4+44=16*4.
All final manifest patches and the scan coordinate model verified;
player retest pending. fix_scene_row_stride.py updates a played build
without replacing settings or saves.

Run fix_remaining_sprite_limits.py after fix_scene_row_stride.py.
0x4157ad: static forward gate 0x1fb0 to 0x3f60.
0x41599f: active render squared distance 0x400000 to 0x1000000.
0x426718: scenery retirement squared radius 0x6400 to 0x19000,
matching 0x425eb8 update gate and exceeding activation 294 squared.
All manifest patch bytes verified; visual retest pending.

Player confirmed the final extended-scene build looks good after the additional sprite drawing limits and scenery retirement correction. Full playthrough remains untested.

Extended soft fog: compile amok_xinput.c with -DAMOK_MOD -DAMOK_FAR_TERRAIN -DAMOK_SOFT_FOG, then run prepare_extended_soft_fog.py once. Terrain smoothstep spans samples 220..279 with palette rows 0..31. Sprite tables span depths 118..147 with rows 0..15. Original level-colored palettes are retained. Palette bounds and monotonicity verified; player test pending.

Fast terrain comparison: add -DAMOK_FAST_TERRAIN to the soft-fog DLL
compile flags, produce work/AMOKMOD-fast-fog.dll, and run
prepare_fast_soft_fog.py once. Loader hook 0x4117a4 invalidates the
8 MiB decoded terrain; renderer entry 0x42036c refreshes changed map
chunks before drawing. Two sampler hooks use native cached lookup.
Synthetic reference parity including boundaries, map changes and
level invalidation passed. Real mission parity and motion pending.

60 FPS comparison: prepare_60fps_soft_fog.py changes only mission
frame limit assignments at 0x417e34 (26) and 0x417e40 (40) to 60.
Elapsed-time simulation scaler at 0x424540 remains byte-identical.
Previous renderer intervals averaged ~24 ms; motion retest pending.

Native terrain staging comparison: add -msse2 -DAMOK_RENDER_PROFILE
-DAMOK_TERRAIN_STAGE to fast soft-fog helper flags. Produce
work/AMOKMOD-stage-fog.dll; run prepare_staged_soft_fog.py once.
Native dimensions and world sample geometry retained. First-frame
direct/staged pixel and occlusion comparison automatically reverts
optimization on mismatches. Synthetic 4,147,200 pixel pairs and
270,720 occlusion pointer conversions verified. Runtime pending.

Native staging runtime comparison: zero pixel-pair and sprite occlusion-pointer mismatches. Sky planes advance with staged columns, retaining original equality behavior for column zero. Terrain drawing averages ~10 ms compared with ~12-14 ms before; full frame intervals ~20-21 ms. Synthetic conversion tests pass with redirected test memory. Player motion confirmation pending.

Player confirmed the full-native-4K staged renderer looks much better. Preferred current build: Amok-2160p-Staged-Soft-Fog-Test, launched by Play-Amok-4K-Staged-Soft-Fog.cmd. Full playthrough remains untested.

Polygon range test: prepare_polygon_range.py copies the staged build. Remaining radius gates 0x415b11/0x415d68 double; 0x4164be/0x4164d4 use 140-depth occlusion and offset 560. A depth guard at 0x4164a3 retains the eight-head sorting bias within allocated storage. Patch bytes and helper branch targets verified; player test pending.

Ray precision experiment: add -DAMOK_RAY_PRECISION to staged helper flags. Hook 0x6a059e distributes signed horizontal ray-spacing division remainders. Recovered numerators must match stock setup; unsupported modes retain original adds. 125,827,200 signed ray positions match exact division. Player comparison pending.
Ray correction runtime active at 1920 paired columns. Native/staged pixels and occlusion entries still match exactly. Terrain cost ~10 ms, total ~20 ms; visual motion and cross-renderer world alignment pending.

Player confirmed ray precision improves turning considerably. Preferred current build: Amok-2160p-Ray-Precision-Test, launched by Play-Amok-4K-Ray-Precision.cmd. Retains confirmed polygon enemy/door fixes, extended range, soft fog, controls and native 4K. Full playthrough remains untested.

Frame delivery comparison: prepare_frame_delivery.py keeps EXE/DLL identical. ddraw.ini maxgameticks=-1 and singlecpu=false; own game mission limit remains 60. Wrapper documented defaults/config: https://github.com/FunkyFr3sh/cnc-ddraw/blob/master/src/config.c . Runtime measurements and gameplay confirmation pending.
Frame delivery runtime: unrestricted process CPU affinity confirmed. Four measured 120-frame blocks averaged 16.55/17.80/17.24/17.77 ms, versus prior typical 20-21 ms. Native staging pixel and occlusion parity remains exact. Occasional frame spikes remain; player visual and gameplay-speed checks pending.

Player confirmed the frame-delivery version feels much smoother. Preferred current build: Amok-2160p-Frame-Delivery-Test, launched by Play-Amok-4K-Frame-Delivery.cmd. Retains confirmed ray precision, polygon enemy/door fixes, extended range, soft fog, controller support and native 4K. Full playthrough remains untested.
