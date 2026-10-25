param(
    [Parameter(Mandatory=$true)][string]$CompilerPath,
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'build')
)
$ErrorActionPreference = 'Stop'
$compiler = (Resolve-Path -LiteralPath $CompilerPath).Path
$destination = [System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $destination -Force | Out-Null
& $compiler -shared -o (Join-Path $destination 'farmex_vitals_bridge.dll') (Join-Path $PSScriptRoot 'vitals_bridge.c') (Join-Path $PSScriptRoot 'image_identity.c') (Join-Path $PSScriptRoot 'shared_vitals.c') -lkernel32
if ($LASTEXITCODE -ne 0) { throw 'DLL derlemesi başarısız.' }
& $compiler -o (Join-Path $destination 'farmex_probe_host.exe') (Join-Path $PSScriptRoot 'probe_host.c') -lkernel32
if ($LASTEXITCODE -ne 0) { throw 'Yerel test programı derlemesi başarısız.' }
Get-FileHash -LiteralPath (Join-Path $destination 'farmex_vitals_bridge.dll'), (Join-Path $destination 'farmex_probe_host.exe') -Algorithm SHA256
