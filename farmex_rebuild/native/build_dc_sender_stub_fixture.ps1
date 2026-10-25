param(
    [Parameter(Mandatory=$true)][string]$CompilerPath,
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
$compiler = (Resolve-Path -LiteralPath $CompilerPath).Path
$destination = [System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $destination -Force | Out-Null
& $compiler -o (Join-Path $destination 'dc_sender_stub_fixture.exe') (Join-Path $PSScriptRoot 'dc_sender_stub_fixture.c') -lkernel32
if ($LASTEXITCODE -ne 0) { throw 'Own x86 sender fixture build failed.' }
Get-FileHash -LiteralPath (Join-Path $destination 'dc_sender_stub_fixture.exe') -Algorithm SHA256
