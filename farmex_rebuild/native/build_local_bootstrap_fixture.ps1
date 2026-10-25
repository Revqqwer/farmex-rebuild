param(
    [Parameter(Mandatory=$true)][string]$CompilerPath,
    [Parameter(Mandatory=$true)][string]$BridgePath,
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'local-bootstrap-build'),
    [switch]$SourceWorker
)
$ErrorActionPreference = 'Stop'
$compiler = (Resolve-Path -LiteralPath $CompilerPath).Path
$bridge = (Resolve-Path -LiteralPath $BridgePath).Path
$expected = '4510845E33931B26DA0381ADFA12E414C4EF72D9C0206728952F6ECFE1903C3A'
if ((Get-FileHash -LiteralPath $bridge -Algorithm SHA256).Hash -ne $expected) {
    throw 'This local experiment accepts only the pinned own bridge build.'
}
$destination = [System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $destination -Force | Out-Null
$bytes = [System.IO.File]::ReadAllBytes($bridge)
$body = 'static const BYTE own_bridge_image[] = {' + (($bytes | ForEach-Object { '0x{0:x2}' -f $_ }) -join ',') + '};'
[System.IO.File]::WriteAllText((Join-Path $destination 'own_bridge_image.h'),$body,[System.Text.Encoding]::ASCII)
$sourceOptions = @()
if ($SourceWorker) { $sourceOptions += '-DFARMEX_SOURCE_LOADER_WORKER' }
& $compiler @sourceOptions ('-I' + $destination) -o (Join-Path $destination 'farmex_probe_host.exe') (Join-Path $PSScriptRoot 'local_bootstrap_fixture.c') -lkernel32
if ($LASTEXITCODE -ne 0) { throw 'Own local bootstrap host build failed.' }
Get-FileHash -LiteralPath (Join-Path $destination 'farmex_probe_host.exe') -Algorithm SHA256
