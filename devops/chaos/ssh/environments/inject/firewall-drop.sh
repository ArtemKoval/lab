#!/bin/bash
# Drop the packets on the forwarded port.
set -eu
iptables -A INPUT -p tcp --dport 22 -j DROP
