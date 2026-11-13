#!/bin/bash
# Disable agent forwarding on the server.
set -eu
printf "AllowAgentForwarding no\n" > /etc/chaos/sshd_extra.d/10-agent.conf
kill "$(cat /run/sshd-practice.pid)"
/usr/sbin/sshd -f /etc/chaos/sshd_practice.conf
