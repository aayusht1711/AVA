#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$DIR/ava.pid" ]; then
  kill $(cat "$DIR/ava.pid") 2>/dev/null
  rm "$DIR/ava.pid"
  echo "AVA backend stopped."
else
  echo "No AVA process found."
fi
