#!/usr/bin/env bash
set -euo pipefail
# Start this in the container after confirming the simulator and bridges.
# The rectangle must fit the CURRENT X11 screen (check xrandr).
: "${DISPLAY:=:0}"
SIZE=${CAPTURE_SIZE:-776x630}
OFFSET=${CAPTURE_OFFSET:-522,275}
OUT=${1:-recording}
mkdir -p "$OUT"
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ffmpeg -y -f x11grab -framerate 15 -video_size "$SIZE" -i "${DISPLAY}+${OFFSET}" \
  -c:v libx264 -preset ultrafast -crf 18 -pix_fmt yuv420p "$OUT/raw.mp4" >"$OUT/ffmpeg.log" 2>&1 &
REC_PID=$!
cleanup() { kill -INT "$REC_PID" 2>/dev/null || true; wait "$REC_PID" || true; }
trap cleanup EXIT
sleep 3
python3 "$SCRIPT_DIR/ai_patrol.py" '近くを巡回して' | tee "$OUT/patrol.log"
sleep 5
