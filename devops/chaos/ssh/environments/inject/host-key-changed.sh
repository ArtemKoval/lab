#!/bin/bash
# Regenerate the practice host key and restart the daemon.
set -eu
rm -f /etc/chaos/practice_hostkey /etc/chaos/practice_hostkey.pub
ssh-keygen -t ed25519 -N "" -q -f /etc/chaos/practice_hostkey
kill "$(cat /run/sshd-practice.pid)"
/usr/sbin/sshd -f /etc/chaos/sshd_practice.conf
