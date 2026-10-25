param(
    [Parameter(Mandatory=$true)][string]$CompilerPath,
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'lifecycle-build')
)
$ErrorActionPreference = 'Stop'
$compiler = (Resolve-Path -LiteralPath $CompilerPath).Path
$destination = [System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $destination -Force | Out-Null
& $compiler -shared -o (Join-Path $destination 'farmex_vitals_bridge.dll') (Join-Path $PSScriptRoot 'vitals_bridge.c') (Join-Path $PSScriptRoot 'image_identity.c') (Join-Path $PSScriptRoot 'shared_vitals.c') -lkernel32
if ($LASTEXITCODE -ne 0) { throw 'Lifecycle DLL build failed.' }
& $compiler -o (Join-Path $destination 'farmex_probe_host.exe') (Join-Path $PSScriptRoot 'lifecycle_fixture_host.c') -lkernel32
if ($LASTEXITCODE -ne 0) { throw 'Lifecycle host build failed.' }
Get-FileHash -LiteralPath (Join-Path $destination 'farmex_vitals_bridge.dll'), (Join-Path $destination 'farmex_probe_host.exe') -Algorithm SHA256
