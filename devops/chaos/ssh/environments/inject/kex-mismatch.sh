#!/bin/bash
# Restrict the server to a legacy key exchange set.
set -eu
printf "KexAlgorithms diffie-hellman-group14-sha1\n" > /etc/chaos/sshd_extra.d/10-kex.conf
kill "$(cat /run/sshd-practice.pid)"
/usr/sbin/sshd -f /etc/chaos/sshd_practice.conf
