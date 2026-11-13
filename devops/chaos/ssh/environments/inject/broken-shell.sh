#!/bin/bash
# Set the shell of the practice account to /bin/false.
set -eu
usermod -s /bin/false practice
