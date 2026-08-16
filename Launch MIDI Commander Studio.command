#!/bin/zsh

set -u

STUDIO_ROOT="${0:A:h}"
STUDIO_VENV="$STUDIO_ROOT/.studio-venv"
STUDIO_RUNTIME="$STUDIO_ROOT/.studio-runtime"
STUDIO_URL="http://127.0.0.1:8765"

mkdir -p "$STUDIO_RUNTIME"

if /usr/bin/curl --silent --fail "$STUDIO_URL/api/health" >/dev/null 2>&1; then
  /usr/bin/open "$STUDIO_URL"
  exit 0
fi

if ! command -v python3 >/dev/null 2>&1; then
  /usr/bin/osascript -e 'display alert "Python 3 is required" message "Install Python 3, then launch MIDI Commander Studio again." as critical'
  exit 1
fi

if [[ ! -x "$STUDIO_VENV/bin/python" ]]; then
  echo "Preparing MIDI Commander Studio for first use…"
  python3 -m venv "$STUDIO_VENV" || exit 1
fi

if ! "$STUDIO_VENV/bin/python" -c 'import fastapi, mido, rtmidi, uvicorn' >/dev/null 2>&1; then
  echo "Installing Studio components…"
  if ! "$STUDIO_VENV/bin/python" -m pip install --disable-pip-version-check -r "$STUDIO_ROOT/studio/requirements.txt" >"$STUDIO_RUNTIME/install.log" 2>&1; then
    /usr/bin/osascript -e 'display alert "Studio setup failed" message "Open .studio-runtime/install.log in the repository folder for details." as critical'
    exit 1
  fi
fi

cd "$STUDIO_ROOT" || exit 1
nohup "$STUDIO_VENV/bin/python" -m studio.backend.app >"$STUDIO_RUNTIME/server.log" 2>&1 &
echo $! >"$STUDIO_RUNTIME/server.pid"

for attempt in {1..80}; do
  if /usr/bin/curl --silent --fail "$STUDIO_URL/api/health" >/dev/null 2>&1; then
    /usr/bin/open "$STUDIO_URL"
    exit 0
  fi
  sleep 0.15
done

/usr/bin/osascript -e 'display alert "Studio did not start" message "Open .studio-runtime/server.log in the repository folder for details." as critical'
exit 1
