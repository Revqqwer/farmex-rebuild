param(
    [Parameter(Mandatory=$true)][string]$CompilerPath,
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
$compiler = (Resolve-Path -LiteralPath $CompilerPath).Path
$destination = [System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $destination -Force | Out-Null
& $compiler -o (Join-Path $destination 'profile_api_fixture.exe') (Join-Path $PSScriptRoot 'profile_api_fixture.c') -lkernel32
if ($LASTEXITCODE -ne 0) { throw 'Owned profile API fixture build failed.' }
Get-FileHash -LiteralPath (Join-Path $destination 'profile_api_fixture.exe') -Algorithm SHA256
