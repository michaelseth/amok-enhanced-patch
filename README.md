# AMOK Enhanced 4K

Patch source, verified sparse executable changes, installer, and configuration for the preserved 0.1.0 preview. Supply your own matching Windows 95 AMOK game and data.

## Install

Download the patch ZIP from Releases, extract it, and run Apply-Amok-Patch.cmd. Select the original game and a new output folder. The installer verifies the game data and creates a separate portable copy. See [installation details](docs/INSTALL.txt).

## Included changes

Native 3840 x 2160 rendering; terrain alignment and precision; optimized terrain renderer; extended terrain, sprite and polygon range; soft distance fog; smaller HUD; camera-specific overlay alignment; XInput controls; improved frame delivery. This is an experimental patch, not a native source port. A full playthrough and testing on a separate clean PC remain outstanding.

## Repository contents

- source/: helper C source and original patch-package builder.
- patch-manifest.json: byte changes, supported hashes, game-data hashes, and payload hashes. No complete game executable or assets.
- Apply-Patch.ps1 and Apply-Amok-Patch.cmd: installer source.
- payload/: text configuration, launcher, guide, and cnc-ddraw license. DLLs are release attachments, excluded from Git.
- research/: preserved development scripts and notes; these require the original research workspace layout and dependencies.

## Build the helper

Use Windows PowerShell and LLVM/MinGW clang with 32-bit Windows headers and libraries:

```powershell
.\Build-Helper.ps1
```

This builds build/AMOKMOD.dll and runs controller mapping checks. The exact historical helper is preserved in the release; a rebuilt DLL may have a different hash because the compiler and PE timestamps differ. The installer intentionally rejects a helper whose hash differs from the manifest. Regenerate the manifest with source/build_patch.py when updating the payload. See [package build notes](source/BUILD-NOTES.txt).

The root installer expects the complete release payload. A source checkout alone does not include the DLLs. Obtain them from the matching release, preserving its payload layout. To generate the exact enhanced executable from player-supplied originals, apply the checked-in sparse manifest through the installer.

## Supported executable

Original SHA-256: `09d505057e4fadf894100c332631137f7861de83c0f3606e067e7a55d3d0eb33`

Patched SHA-256: `d097724e98152deafe253006421667344062c288c5784f4c5793247c5b68735b`

## Notices

No custom-code license is selected. cnc-ddraw retains its included MIT license. Original game files, saves, captures, diagnostic catalogs, and experimental build copies stay outside Git. Existing development folders remain intact.
