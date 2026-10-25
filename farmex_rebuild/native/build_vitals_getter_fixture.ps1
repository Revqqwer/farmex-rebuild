param(
 [Parameter(Mandatory=$true)][string]$CompilerPath,
 [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference='Stop'
$compiler=(Resolve-Path -LiteralPath $CompilerPath).Path
$destination=[System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $destination -Force | Out-Null
& $compiler -o (Join-Path $destination 'vitals_getter_fixture.exe') (Join-Path $PSScriptRoot 'vitals_getter_fixture.c') -lkernel32
if ($LASTEXITCODE -ne 0) { throw 'Owned HP/MP getter fixture build failed.' }
Get-FileHash -LiteralPath (Join-Path $destination 'vitals_getter_fixture.exe') -Algorithm SHA256
