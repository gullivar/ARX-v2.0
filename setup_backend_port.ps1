$ErrorActionPreference = "Stop"

Write-Host "Configuring Port Forwarding for 8000 (Backend)..."

# 1. Open Firewall Port 8000
$Port = 8000
$RuleName = "WSL_Backend_Access"

$ExistingRule = Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue
if (-not $ExistingRule) {
    Write-Host "Creating Firewall Rule for Port $Port..."
    New-NetFirewallRule -DisplayName $RuleName -Direction Inbound -LocalPort $Port -Protocol TCP -Action Allow
} else {
    Write-Host "Firewall rule exists."
}

# 2. Get WSL IP Address
$WslIp = wsl -d ARX-Ubuntu -u root -e hostname -I
$WslIp = $WslIp.Trim()

if (-not $WslIp) {
    Write-Error "Could not allow detect WSL IP."
    exit 1
}

Write-Host "WSL IP detected: $WslIp"

# 3. Add PortProxy
Write-Host "Adding PortProxy: 0.0.0.0:8000 -> $WslIp:8000"
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$WslIp

Write-Host "---PORT-FORWARDING-COMPLETE---"
netsh interface portproxy show all
