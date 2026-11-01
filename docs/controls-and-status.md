# AMOK native Windows enhancement prototype

The latest 4:3 build is **Play-Amok-4K-4x3.cmd**. Its updated controls and
terrain-projection repair are described in **Amok-2160p-4x3-Test/README.md**.
The widescreen builds below retain their earlier controls.

Launch **Play-Amok-4K.cmd** for a 3840×2160 render surface, or
**Play-Amok-1080p.cmd** for 1920×1080. The launcher closes only other test
copies under this outputs folder, so one AMOK test runs at a time.
The original C:\Amok files were not modified.

## Xbox controller

| Controller input | Stock game action |
| --- | --- |
| Left stick / D-pad | Move forward/back and turn; navigate menus |
| Right stick horizontal | Turn |
| A | Enter: select in menus / throw bomb in a mission |
| B or Start | Escape: menu/back/skip, depending on game state |
| Right trigger or RB | Ctrl: minigun |
| Left trigger or X | Space: normal missile |
| Y | Backspace: heavy missile |
| LB held with turn | Alt: sidestep |
| Left stick click held | Shift: run |
| View / Back | Tab: mission map |

Movement currently uses the stock digital key bindings. It is not analog
movement or modern free aiming. If you change the game's keyboard bindings,
the controller mapping will need corresponding changes. Keyboard controls
remain available. Controller input is gated to AMOK's foreground window and
released on disconnection or loss of focus. The first connected XInput pad
among slots 0–3 is used. controller-status.txt records detection status.

## What has been checked

- Native 32-bit Windows execution with cnc-ddraw 7.1 for DirectDraw compatibility.
- 1920×1080 and 3840×2160 display parameters read from the running game.
- At 4K, framebuffer stride is 7680 bytes for the game's 16-bit pixels.
- A 4K 3D scene observed after expanding working buffers and sprite tables.
- Xbox controller detected in XInput slot 0; mapping logic tests pass.

This remains an experimental build. A short rendering check is not a full
playthrough; physical controller operation, mission transitions, save/load,
sound and all camera modes still need user testing. Original textures and HUD
art remain low resolution. The game retains its original black bands above
and below the 3D view (the 4K 3D viewport is 3840×1800 inside the 2160-line
surface). The intro/menu scaling patch chooses the largest integer scale
that fits, but menu navigation and layout still need confirmation.

CD music initialization is skipped; no replacement soundtrack is included.
The modified EXE is fixed at its original preferred address, as required by
the absolute-address runtime patches. These builds force their selected
resolution; the original resolution hotkeys do not select a different mode.

pcrecomp was used to inspect and catalog the executable, not to produce a
complete source recompilation. The current work patches the original native
executable and adds an in-process XInput DLL.

Verified 4K widescreen build: launch Play-Amok-4K-Widescreen-Fixed.cmd. Player confirmed terrain/sprite alignment, controller controls, compass/waypoint alignment across all three camera views, and the smaller HUD. Native render surface: 3840x2160. Original horizontal field of view is retained. A full playthrough remains untested.
