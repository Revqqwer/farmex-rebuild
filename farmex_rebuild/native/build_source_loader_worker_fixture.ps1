param(
 [Parameter(Mandatory=$true)][string]$CompilerPath,
 [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference='Stop'
$compiler=(Resolve-Path -LiteralPath $CompilerPath).Path
$destination=[System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $destination -Force | Out-Null
& $compiler -o (Join-Path $destination 'source_loader_worker_fixture.exe') (Join-Path $PSScriptRoot 'source_loader_worker_fixture.c') -lkernel32
if ($LASTEXITCODE -ne 0) { throw 'Owned source-loader-worker fixture build failed.' }
Get-FileHash -LiteralPath (Join-Path $destination 'source_loader_worker_fixture.exe') -Algorithm SHA256
