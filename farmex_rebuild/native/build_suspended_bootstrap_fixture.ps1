param(
    [Parameter(Mandatory=$true)][string]$CompilerPath,
    [Parameter(Mandatory=$true)][string]$BridgePath,
    [Parameter(Mandatory=$true)][string]$PythonPath,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [switch]$TransferImage,
    [switch]$CopiedWorker,
    [switch]$RejectImage,
    [switch]$SourceWorker,
    [switch]$RejectSourceImage,
    [switch]$RejectSourceAPI
)
$ErrorActionPreference='Stop'
if($SourceWorker -and ($CopiedWorker -or $RejectImage)) { throw 'Source worker and copied-worker modes are separate.' }
if(($RejectSourceImage -or $RejectSourceAPI) -and -not $SourceWorker) { throw 'Source negative controls require SourceWorker.' }
if($RejectSourceImage -and $RejectSourceAPI) { throw 'Use one source negative control per build.' }
if($RejectImage -and -not $CopiedWorker) { throw 'RejectImage is only the explicit copied-worker negative control.' }
$compiler=(Resolve-Path -LiteralPath $CompilerPath).Path
$bridge=(Resolve-Path -LiteralPath $BridgePath).Path
$python=(Resolve-Path -LiteralPath $PythonPath).Path
if((Get-FileHash -LiteralPath $bridge -Algorithm SHA256).Hash -ne '4510845E33931B26DA0381ADFA12E414C4EF72D9C0206728952F6ECFE1903C3A') { throw 'Only pinned own bridge accepted.' }
$destination=[System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $destination -Force | Out-Null
$bytes=[System.IO.File]::ReadAllBytes($bridge)
$header='static const BYTE own_bridge_image[] = {'+(($bytes | ForEach-Object {'0x{0:x2}' -f $_}) -join ',')+'};'
[System.IO.File]::WriteAllText((Join-Path $destination 'own_bridge_image.h'),$header,[System.Text.Encoding]::ASCII)
$childOptions=@('-DFARMEX_SUSPENDED_CHILD')
$parentOptions=@()
if($SourceWorker) {
    $TransferImage=$true
    $childOptions+='-DFARMEX_SOURCE_WORKER_CHILD';$parentOptions+='-DFARMEX_SOURCE_WORKER_PARENT'
}
if($RejectSourceImage) { $parentOptions+='-DFARMEX_SOURCE_BAD_IMAGE' }
if($RejectSourceAPI) { $parentOptions+='-DFARMEX_SOURCE_BAD_API' }
if($CopiedWorker) {
    $TransferImage=$true
    $childOptions+='-DFARMEX_COPIED_WORKER_CHILD';$parentOptions+='-DFARMEX_COPIED_WORKER_PARENT'
    & $compiler -o (Join-Path $destination 'farmex_worker_template.exe') (Join-Path $PSScriptRoot 'copied_worker.c') -lkernel32
    if($LASTEXITCODE -ne 0) {throw 'Own worker template build failed.'}
    & $python (Join-Path $PSScriptRoot 'prepare_copied_worker.py') (Join-Path $destination 'farmex_worker_template.exe') $destination
    if($LASTEXITCODE -ne 0) {throw 'Own worker extraction failed.'}
}
if($RejectImage) { $parentOptions+='-DFARMEX_BAD_WORKER_REFERENCE' }
if($TransferImage) { $childOptions+='-DFARMEX_TRANSFER_CHILD';$parentOptions+='-DFARMEX_TRANSFER_PARENT' }
& $compiler @childOptions ('-I'+$destination) -o (Join-Path $destination 'farmex_probe_host.exe') (Join-Path $PSScriptRoot 'local_bootstrap_fixture.c') -lkernel32
if($LASTEXITCODE -ne 0) {throw 'Own suspended child build failed.'}
$pinOptions=@()
if($SourceWorker) { $pinOptions+='--source-worker' }
& $python (Join-Path $PSScriptRoot 'prepare_bootstrap_child.py') (Join-Path $destination 'farmex_probe_host.exe') (Join-Path $destination 'own_bootstrap_child.h') @pinOptions
if($LASTEXITCODE -ne 0) {throw 'Own child pin generation failed.'}
& $compiler @parentOptions ('-I'+$destination) -o (Join-Path $destination 'farmex_launch_fixture.exe') (Join-Path $PSScriptRoot 'suspended_bootstrap_parent.c') (Join-Path $PSScriptRoot 'image_identity.c') -lkernel32
if($LASTEXITCODE -ne 0) {throw 'Own suspended parent build failed.'}
Get-FileHash -LiteralPath (Join-Path $destination 'farmex_launch_fixture.exe'),(Join-Path $destination 'farmex_probe_host.exe') -Algorithm SHA256
