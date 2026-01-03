$ErrorActionPreference = "Stop"

Write-Host "Configuring Port Forwarding for 5173 (Frontend)..."

# 1. Open Firewall Port 5173
$Port = 5173
$RuleName = "WSL_Frontend_Access"

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
Write-Host "Adding PortProxy: 0.0.0.0:5173 -> $WslIp:5173"
netsh interface portproxy add v4tov4 listenport=5173 listenaddress=0.0.0.0 connectport=5173 connectaddress=$WslIp

Write-Host "---PORT-FORWARDING-COMPLETE---"
netsh interface portproxy show all
