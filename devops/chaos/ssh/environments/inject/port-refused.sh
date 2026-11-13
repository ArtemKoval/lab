#!/bin/bash
# Stop the practice sshd.
set -eu
kill "$(cat /run/sshd-practice.pid)"
