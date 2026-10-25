param(
 [Parameter(Mandatory=$true)][string]$CompilerPath,
 [string]$OutputDirectory = (Join-Path $PSScriptRoot 'callback-slot-build')
)
$ErrorActionPreference='Stop'
$compiler=(Resolve-Path -LiteralPath $CompilerPath).Path
$destination=[System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $destination -Force | Out-Null
& $compiler -o (Join-Path $destination 'farmex_callback_slot_fixture.exe') (Join-Path $PSScriptRoot 'callback_slot_fixture.c') -lkernel32
if ($LASTEXITCODE -ne 0) { throw 'Own x86 callback slot fixture build failed.' }
Get-FileHash -LiteralPath (Join-Path $destination 'farmex_callback_slot_fixture.exe') -Algorithm SHA256
