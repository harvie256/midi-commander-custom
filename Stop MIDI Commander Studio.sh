#!/usr/bin/env bash

STUDIO_URL="http://127.0.0.1:8765"

notify() {
  echo "$1"
  if command -v notify-send >/dev/null 2>&1; then
    notify-send "MIDI Commander Studio" "$1" >/dev/null 2>&1
  fi
}

if curl --silent --fail -X POST "$STUDIO_URL/api/shutdown" >/dev/null 2>&1; then
  notify "The local service has stopped."
else
  notify "The Studio was not running."
fi
