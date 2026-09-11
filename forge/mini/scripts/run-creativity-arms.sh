#!/bin/bash
# CREATIVITY-ARMS-1, v2. Segments run IN ORDER within an arm: the carry does not exist otherwise.
# v1 continued silently past a segment that died at its first stage, so F's carry never accumulated
# and the arms measured a hole rather than a return path. A segment that does not reach RUN_ENDED is
# now retried once and then reported loudly.
cd /home/user/h-EPI
S=/tmp/claude-0/-home-user-h-EPI/8bf872c3-0c47-568f-9b7b-a4f71565d7f0/scratchpad
export OLLAMA_API_KEY="${OLLAMA_API_KEY:?set it in the environment; it is never written to a file in this repository}"
LOGS=$S/arms-logs; mkdir -p $LOGS
MODEL=deepseek-v4-pro:0813
one_segment () {
  arm=$1; i=$2; idx=$(printf "s%02d" $i); prev=$(printf "s%02d" $((i-1)))
  PYTHONPATH=src python tools/creativity_arms.py install --arm "$arm" --index "$i" \
    --runs forge/mini/runs/creativity --out forge/mini/manifests/creativity >> "$LOGS/$arm.log" 2>&1
  # Preflight before paying for a single call: a seat the tool does not register cost 36 runs once
  # and 3 more a second time, and both were visible here.
  if ! PYTHONPATH=src python tools/creativity_arms.py alarms \
        --manifest "forge/mini/manifests/creativity/$arm/$idx/manifest.json" >> "$LOGS/$arm.log" 2>&1; then
    echo "!! $arm/$idx FAILED PREFLIGHT -- not spending calls on it" | tee -a "$LOGS/$arm.log"
    return 1
  fi
  PYTHONPATH=src timeout 2400 python tools/run_mini.py live \
    --manifest "forge/mini/manifests/creativity/$arm/$idx/manifest.json" --model $MODEL \
    --output-dir "forge/mini/runs/creativity/$arm/$idx" --timeout-seconds 900 --retries 2 \
    >> "$LOGS/$arm.log" 2>&1
  # Read the finished segment before building the next one. A starved loop, an artifact id where a
  # function name belongs, or a stalled carry all stop the arm here rather than after eight segments.
  PYTHONPATH=src python tools/creativity_arms.py alarms \
    --segment "forge/mini/runs/creativity/$arm/$idx" \
    --previous-brief "forge/mini/manifests/creativity/$arm/$prev/proposed_organisation.txt" \
    --brief "forge/mini/manifests/creativity/$arm/$idx/proposed_organisation.txt" | tee -a "$LOGS/$arm.log"
  alarm=${PIPESTATUS[0]}
  if [ "$alarm" -ne 0 ]; then
    echo "!! $arm/$idx raised a FATAL alarm -- stopping this arm" | tee -a "$LOGS/$arm.log"
    return 2
  fi
  grep -q RUN_ENDED "forge/mini/runs/creativity/$arm/$idx/log.jsonl" 2>/dev/null
}
run_arm () {
  arm=$1; n=$2
  for i in $(seq 0 $((n-1))); do
    idx=$(printf "s%02d" $i)
    if [ -d "forge/mini/runs/creativity/$arm/$idx" ]; then
      grep -q RUN_ENDED "forge/mini/runs/creativity/$arm/$idx/log.jsonl" 2>/dev/null && continue
      rm -rf "forge/mini/runs/creativity/$arm/$idx"
    fi
    one_segment "$arm" "$i"; rc=$?
    if [ "$rc" -eq 2 ]; then
      echo "!! $arm stopped at $idx on a fatal alarm; the rest of the arm is not run" | tee -a "$LOGS/$arm.log"
      break
    elif [ "$rc" -ne 0 ]; then
      echo "!! $arm/$idx did not end; retrying once" >> "$LOGS/$arm.log"
      rm -rf "forge/mini/runs/creativity/$arm/$idx"
      one_segment "$arm" "$i" || echo "!! $arm/$idx DIED TWICE -- the carry past it is a hole" >> "$LOGS/$arm.log"
    fi
  done
  ended=$(for d in forge/mini/runs/creativity/$arm/s*/; do grep -q RUN_ENDED "$d/log.jsonl" 2>/dev/null && echo x; done | wc -l)
  echo "$arm done: $ended/$n reached RUN_ENDED"
}
#run_arm S 1 &
#run_arm R 6 &
#run_arm N 8 &
#run_arm F 8 &
#run_arm W 8 &
run_arm A 8 &
wait
echo "CREATIVITY-ARMS-1 v2 COMPLETE"
