param([string]$Compiler='clang')
$ErrorActionPreference='Stop'
$build=Join-Path $PSScriptRoot 'build'
New-Item -ItemType Directory -Path $build -Force|Out-Null
& $Compiler --target=i686-w64-mingw32 -shared -O2 -mstackrealign -msse2 -DAMOK_MOD -DAMOK_FAR_TERRAIN -DAMOK_SOFT_FOG -DAMOK_FAST_TERRAIN -DAMOK_RENDER_PROFILE -DAMOK_TERRAIN_STAGE -DAMOK_RAY_PRECISION (Join-Path $PSScriptRoot 'source/amok_xinput.c') -o (Join-Path $build 'AMOKMOD.dll') -luser32
if($LASTEXITCODE -ne 0){throw 'Helper build failed'}
& $Compiler --target=i686-w64-mingw32 -O2 (Join-Path $PSScriptRoot 'source/amok_xinput.c') -o (Join-Path $build 'controller-tests.exe') -luser32
if($LASTEXITCODE -ne 0){throw 'Test build failed'}
& (Join-Path $build 'controller-tests.exe')
if($LASTEXITCODE -ne 0){throw 'Helper tests failed'}
Write-Host "Built helper and passed input tests in $build"
