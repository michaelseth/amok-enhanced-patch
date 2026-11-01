AMOK Enhanced 4K - Patch-only preview 0.1.0

This download contains no complete AMOK executable or game assets.
You supply the supported original Windows 95 game and its data files.

HOW TO APPLY
1. Extract this patch ZIP completely.
2. Double-click Apply-Amok-Patch.cmd.
3. Choose your original game folder, AMOKFILS folder, or extracted CD root.
4. Choose where to create a separate AMOK-Enhanced-4K folder.
5. In that new folder, double-click Play-Amok.cmd.

No Python, compiler, installer or administrator access is required.
Windows PowerShell, included with Windows 10/11, runs the patcher.
Keep all patch files together. The destination must not already exist.
Your source files are read and copied; they are never patched in place.
The resulting game folder is portable and can be moved as a whole.

SUPPORTED EDITION
Currently supports the Windows 95 AMOK.BIN whose SHA-256 is:
09d505057e4fadf894100c332631137f7861de83c0f3606e067e7a55d3d0eb33
An identical file named AMOK.EXE is also accepted. The complete matching
game data is required. The patcher checks every required data file.
Other editions, translated/modified data, DOS-only installs, previously
patched executables, and incomplete installs are rejected without changes.

INCLUDED FIXES
Modern Windows executable compatibility and CD-check removal.
Native 3840 x 2160 rendering scaled to your display.
Terrain and sprite alignment, terrain precision and renderer optimization.
Extended terrain, sprite and polygon draw distance with gentle edge fog.
Smaller HUD and camera-specific compass/waypoint alignment corrections.
Xbox/XInput controls, run toggle, strafing and camera change button.
Improved frame delivery with a 60 FPS presentation cap.
The resulting game's README.txt contains the controller guide.

VALIDATION AND LIMITS
Preview release based on player-confirmed improvements. Performance varies
by scene and computer; 60 FPS is not guaranteed. A full playthrough and
testing on a separate clean Windows PC are still outstanding.
The patcher verifies both original and resulting executable hashes and
refuses to overwrite existing output. No network connection is used.

COMMAND-LINE USE
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Apply-Patch.ps1 -NoGui -Source "D:\AMOKFILS" -Destination "C:\Games\AMOK-Enhanced-4K"

CREDITS AND SOURCE
AMOK is the original game by Scavenger; game files are player-supplied.
Display compatibility uses cnc-ddraw by FunkyFr3sh and contributors:
https://github.com/FunkyFr3sh/cnc-ddraw
Its MIT license is included in payload\Game\cnc-ddraw-LICENSE.txt.
Source includes the patch installer, package builder and enhancement helper.
No public license for the custom code has been selected in this preview.
No claim of publisher endorsement or permission is made by this package.
