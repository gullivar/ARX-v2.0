$ErrorActionPreference = "Stop"

Write-Host "Configuring Windows Firewall and Port Forwarding for WSL..."

# 1. Open Firewall Port 2222
$Port = 2222
$RuleName = "WSL_SSH_Access"

$ExistingRule = Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue
if (-not $ExistingRule) {
    Write-Host "Creating Firewall Rule for Port $Port..."
    New-NetFirewallRule -DisplayName $RuleName -Direction Inbound -LocalPort $Port -Protocol TCP -Action Allow
} else {
    Write-Host "Firewall rule exists."
}

# 2. Get WSL IP Address
Write-Host "Detecting WSL IP Address..."
# We need to make sure WSL is running first
wsl -d ARX-Ubuntu -u root -e service ssh start
$WslIp = wsl -d ARX-Ubuntu -u root -e hostname -I
$WslIp = $WslIp.Trim()

if (-not $WslIp) {
    Write-Error "Could not allow detect WSL IP. Is WSL running?"
    exit 1
}

Write-Host "WSL IP detected: $WslIp"

# 3. Add PortProxy
Write-Host "Adding PortProxy v4tov4: 0.0.0.0:2222 -> $WslIp:22"
netsh interface portproxy add v4tov4 listenport=2222 listenaddress=0.0.0.0 connectport=22 connectaddress=$WslIp

Write-Host "---PORT-FORWARDING-COMPLETE---"
Write-Host "You can now SSH to WindowsIP:2222 to reach WSL."
# Verify
netsh interface portproxy show all
