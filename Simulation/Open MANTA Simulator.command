#!/bin/zsh

cd "$(dirname "$0")/.." || exit 1

port=8000
log_file="/tmp/manta-simulator-http.log"
python3 -m http.server "$port" --bind 127.0.0.1 >"$log_file" 2>&1 &
server_pid=$!

cleanup() {
  kill "$server_pid" 2>/dev/null
}
trap cleanup EXIT INT TERM

sleep 1
if ! kill -0 "$server_pid" 2>/dev/null; then
  echo "The simulator server could not start. See $log_file"
  cat "$log_file"
  read -r "?Press Return to close."
  exit 1
fi

open "http://127.0.0.1:$port/Simulation/"
echo "MANTA simulator running at http://127.0.0.1:$port/Simulation/"
echo "Keep this window open. Press Control-C to stop the server."
wait "$server_pid"
