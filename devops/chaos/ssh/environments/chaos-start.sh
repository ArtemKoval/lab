#!/bin/bash
# Start the practice sshd and the decoy sshd with fresh host keys.
# The script runs at every container start, so every scenario begins
# from a clean daemon state.
set -eu

mkdir -p /run/sshd

# Fresh practice host key on every start.
rm -f /etc/chaos/practice_hostkey /etc/chaos/practice_hostkey.pub
ssh-keygen -t ed25519 -N "" -q -f /etc/chaos/practice_hostkey

# Fresh decoy host key on every start.
rm -f /etc/chaos/decoy_hostkey /etc/chaos/decoy_hostkey.pub
ssh-keygen -t ed25519 -N "" -q -f /etc/chaos/decoy_hostkey

cat > /etc/chaos/sshd_practice.conf <<'CONF'
# The include comes first: sshd keeps the first value it reads for
# each keyword, so the injection snippets win over the base values.
Include /etc/chaos/sshd_extra.d/*.conf
Port 22
HostKey /etc/chaos/practice_hostkey
PidFile /run/sshd-practice.pid
PasswordAuthentication yes
PermitRootLogin no
AllowUsers practice guest
AuthorizedKeysFile .ssh/authorized_keys
CONF

cat > /etc/chaos/sshd_decoy.conf <<'CONF'
Port 2223
HostKey /etc/chaos/decoy_hostkey
PidFile /run/sshd-decoy.pid
PasswordAuthentication no
PermitRootLogin no
AllowUsers practice
AuthorizedKeysFile .ssh/authorized_keys
Banner /etc/chaos/decoy-banner
CONF

printf 'decoy-ssh: this is not the practice server\n' > /etc/chaos/decoy-banner

# Stop any daemon from a previous start, then start both fresh.
pkill -f "sshd.*sshd_practice.conf" 2>/dev/null || true
pkill -f "sshd.*sshd_decoy.conf" 2>/dev/null || true
rm -f /etc/chaos/sshd_extra.d/*.conf
/usr/sbin/sshd -f /etc/chaos/sshd_practice.conf
/usr/sbin/sshd -f /etc/chaos/sshd_decoy.conf
