#!/bin/bash
# Re-configure SSH to strictly allow Root login
# Make sure previous configs don't conflict
sed -i 's/^PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Ensure the config lines exist if sed missed them (e.g. they were commented out differently)
if ! grep -q "^PermitRootLogin yes" /etc/ssh/sshd_config; then
    echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
fi
if ! grep -q "^PasswordAuthentication yes" /etc/ssh/sshd_config; then
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
fi

# Set root password explicitly again to be sure
echo "root:Nrnwkwls!@12" | chpasswd

# Restart SSH
service ssh restart
echo "SSH Restarted. Root Login Enabled."
