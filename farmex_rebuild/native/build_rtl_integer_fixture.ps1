param(
    [Parameter(Mandatory=$true)][string]$CompilerPath,
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference='Stop'
$compiler=(Resolve-Path -LiteralPath $CompilerPath).Path
if ((Get-FileHash -LiteralPath $compiler -Algorithm SHA256).Hash.ToLowerInvariant() -ne '11b86934bb2833f57fa0453a605ca342aee9207e193faea9b973baa2b2b4c35b') { throw 'Unexpected compiler identity' }
$destination=[System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $destination -Force | Out-Null
& $compiler -o (Join-Path $destination 'rtl_integer_fixture.exe') (Join-Path $PSScriptRoot 'rtl_integer_fixture.c') -lkernel32
if ($LASTEXITCODE -ne 0) { throw 'Own x86 RTL fixture build failed' }
Get-FileHash -LiteralPath (Join-Path $destination 'rtl_integer_fixture.exe') -Algorithm SHA256
