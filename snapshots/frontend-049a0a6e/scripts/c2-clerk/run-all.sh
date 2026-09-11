#!/bin/bash
# Re-run the seven front-end mock test files against the current candidate.
cd /home/aika/.qwenpaw/workspaces/default/work/c2-clerk-login-20260910 || exit 99
export PATH="/home/aika/.nvm/versions/node/v22.22.3/bin:$PATH"
export NODE_OPTIONS="--no-warnings"
total_pass=0
total_fail=0
overall=0
for f in test-entry-rules test-middleware test-bff test-signout test-candidate-shape test-golden-routes test-golden-session; do
  log="/tmp/c2-clerk-fe-${f}.log"
  node --experimental-strip-types "scripts/c2-clerk/${f}.mjs" > "$log" 2>&1
  rc=$?
  line=$(grep -E "passed, [0-9]+ failed" "$log" | tail -1)
  echo "${f} rc=${rc} :: ${line}"
  p=$(echo "$line" | sed -E 's/.*: ([0-9]+) passed.*/\1/')
  fl=$(echo "$line" | sed -E 's/.*passed, ([0-9]+) failed.*/\1/')
  total_pass=$((total_pass + ${p:-0}))
  total_fail=$((total_fail + ${fl:-0}))
  if [ "$rc" -ne 0 ]; then overall=1; fi
done
echo "TOTAL: ${total_pass} passed, ${total_fail} failed, group_rc=${overall}"
exit $overall
