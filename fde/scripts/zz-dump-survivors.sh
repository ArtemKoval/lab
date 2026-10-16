#!/bin/bash
# Temporary: dump the diffs of the surviving mutants.
cd /tmp/fde-mut
PY=/Users/art/Documents/git/lab-fde/fde/.venv/bin/python
"$PY" -m mutmut results 2>&1 | grep "survived" | sed 's/: survived//' > /tmp/s2.txt
while read -r m; do
  echo "=== $m"
  "$PY" -m mutmut show "$m" 2>/dev/null | grep -E "^[-+]" | grep -v "^[-+][-+]" | head -3
done < /tmp/s2.txt
