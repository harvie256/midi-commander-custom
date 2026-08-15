#!/bin/zsh

STUDIO_URL="http://127.0.0.1:8765"

if /usr/bin/curl --silent --fail -X POST "$STUDIO_URL/api/shutdown" >/dev/null 2>&1; then
  /usr/bin/osascript -e 'display notification "The local service has stopped." with title "MIDI Commander Studio"'
else
  /usr/bin/osascript -e 'display notification "The Studio was not running." with title "MIDI Commander Studio"'
fi
