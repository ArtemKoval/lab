#!/bin/bash
# Disable password authentication; the key path stays valid.
set -eu
printf "PasswordAuthentication no\n" > /etc/chaos/sshd_extra.d/10-auth.conf
kill "$(cat /run/sshd-practice.pid)"
/usr/sbin/sshd -f /etc/chaos/sshd_practice.conf
