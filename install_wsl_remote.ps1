$ErrorActionPreference = "Stop"
$WorkingDir = "E:\MyProject\ARX"
New-Item -Path $WorkingDir -ItemType Directory -Force | Out-Null
Set-Location $WorkingDir

Write-Host "[1/5] Downloading Ubuntu 22.04..."
$BundleFile = Join-Path $WorkingDir "ubuntu.zip"
Invoke-WebRequest -Uri "https://aka.ms/wslubuntu2204" -OutFile $BundleFile -UseBasicParsing

Write-Host "[2/5] Extracting Bundle..."
$BundleDir = Join-Path $WorkingDir "bundle_extract"
Expand-Archive -Path $BundleFile -DestinationPath $BundleDir -Force

Write-Host "[3/5] Locating x64 Appx..."
$AppxFileObj = Get-ChildItem -Path $BundleDir -Filter "*x64.appx" | Select-Object -First 1
if (-not $AppxFileObj) {
    Write-Error "Could not find x64.appx in bundle."
    exit 1
}
$AppxZip = $AppxFileObj.FullName + ".zip"
Rename-Item -Path $AppxFileObj.FullName -NewName $AppxZip

Write-Host "[4/5] Extracting Appx to find install.tar.gz..."
$AppxDir = Join-Path $WorkingDir "appx_extract"
Expand-Archive -Path $AppxZip -DestinationPath $AppxDir -Force
$TarFile = Join-Path $AppxDir "install.tar.gz"

if (-not (Test-Path $TarFile)) {
    Write-Error "install.tar.gz not found in Appx."
    exit 1
}

Write-Host "[5/5] Importing Distro 'ARX-Ubuntu' to E:\MyProject\ARX\WSL..."
$WslInstallDir = "E:\MyProject\ARX\WSL"
New-Item -Path $WslInstallDir -ItemType Directory -Force | Out-Null

wsl --import ARX-Ubuntu $WslInstallDir $TarFile

Write-Host "---WSL-INSTALL-COMPLETE---"
wsl -d ARX-Ubuntu -u root -e cat /etc/os-release
