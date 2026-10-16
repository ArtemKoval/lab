#!/bin/bash
# Publish helper: runs gh with the ArtemKoval token from the staged file.
set -e
export GH_TOKEN="$(cat /tmp/gh-token)"
gh "$@"
