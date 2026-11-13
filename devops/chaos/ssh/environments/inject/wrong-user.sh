#!/bin/bash
# Restrict the allowed users to practice.
set -eu
printf "PasswordAuthentication no\nKbdInteractiveAuthentication no\n" > /etc/chaos/sshd_extra.d/10-auth.conf
printf "AllowUsers practice\n" > /etc/chaos/sshd_extra.d/11-allow.conf
kill "$(cat /run/sshd-practice.pid)"
/usr/sbin/sshd -f /etc/chaos/sshd_practice.conf
