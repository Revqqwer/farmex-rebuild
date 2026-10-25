param(
    [Parameter(Mandatory=$true)][string]$CompilerPath,
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'call-build')
)
$ErrorActionPreference = 'Stop'
$compiler = (Resolve-Path -LiteralPath $CompilerPath).Path
$destination = [System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $destination -Force | Out-Null
& $compiler -o (Join-Path $destination 'farmex_call_fixture.exe') (Join-Path $PSScriptRoot 'call_fixture.c') -lkernel32
if ($LASTEXITCODE -ne 0) { throw 'Own32-bit çağrı fixture derlemesi başarısız.' }
Get-FileHash -LiteralPath (Join-Path $destination 'farmex_call_fixture.exe') -Algorithm SHA256
