#!/bin/bash
# Install one practice public key into the practice account. The
# tutor passes the key text as the first argument.
set -eu
KEY_TEXT="$1"
mkdir -p /home/practice/.ssh
printf '%s\n' "$KEY_TEXT" > /home/practice/.ssh/authorized_keys
chown -R practice:practice /home/practice/.ssh
chmod 700 /home/practice/.ssh
chmod 600 /home/practice/.ssh/authorized_keys
