#!/bin/bash
# Remove the practice key and disable password authentication.
set -eu
printf "PasswordAuthentication no\n" > /etc/chaos/sshd_extra.d/10-auth.conf
: > /home/practice/.ssh/authorized_keys
kill "$(cat /run/sshd-practice.pid)"
/usr/sbin/sshd -f /etc/chaos/sshd_practice.conf
