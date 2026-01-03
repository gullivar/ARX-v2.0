#!/bin/bash
mkdir -p /run/sshd
chmod 0755 /run/sshd
/usr/sbin/sshd -D
