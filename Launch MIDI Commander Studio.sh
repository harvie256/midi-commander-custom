#!/usr/bin/env bash

set -u

STUDIO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STUDIO_VENV="$STUDIO_ROOT/.studio-venv-linux"
STUDIO_RUNTIME="$STUDIO_ROOT/.studio-runtime"
STUDIO_URL="http://127.0.0.1:8765"

mkdir -p "$STUDIO_RUNTIME"

report_error() {
  echo "$1: $2" >&2
  if command -v zenity >/dev/null 2>&1; then
    zenity --error --title "$1" --text "$2" >/dev/null 2>&1
  elif command -v notify-send >/dev/null 2>&1; then
    notify-send "$1" "$2" >/dev/null 2>&1
  fi
}

open_studio() {
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$STUDIO_URL" >/dev/null 2>&1 &
  else
    echo "Open $STUDIO_URL in your browser."
  fi
}

if curl --silent --fail "$STUDIO_URL/api/health" >/dev/null 2>&1; then
  open_studio
  exit 0
fi

if ! command -v python3 >/dev/null 2>&1; then
  report_error "Python 3 is required" "Install Python 3 with your package manager, then launch MIDI Commander Studio again."
  exit 1
fi

if [[ ! -x "$STUDIO_VENV/bin/python" ]]; then
  echo "Preparing MIDI Commander Studio for first use…"
  if ! python3 -m venv "$STUDIO_VENV" >"$STUDIO_RUNTIME/venv.log" 2>&1; then
    report_error "Studio setup failed" "Could not create a virtual environment. On Debian/Ubuntu install python3-venv, then try again. Details: .studio-runtime/venv.log"
    exit 1
  fi
fi

if ! "$STUDIO_VENV/bin/python" -c 'import fastapi, mido, pandas, rtmidi, uvicorn' >/dev/null 2>&1; then
  echo "Installing Studio components…"
  if ! "$STUDIO_VENV/bin/python" -m pip install --disable-pip-version-check -r "$STUDIO_ROOT/studio/requirements.txt" >"$STUDIO_RUNTIME/install.log" 2>&1; then
    report_error "Studio setup failed" "Dependency installation failed. Open .studio-runtime/install.log in the repository folder for details. python-rtmidi needs a C++ toolchain and ALSA headers (build-essential, libasound2-dev, libjack-dev) if no wheel is available."
    exit 1
  fi
fi

cd "$STUDIO_ROOT" || exit 1
nohup "$STUDIO_VENV/bin/python" -m studio.backend.app >"$STUDIO_RUNTIME/server.log" 2>&1 &
echo $! >"$STUDIO_RUNTIME/server.pid"

for _ in {1..80}; do
  if curl --silent --fail "$STUDIO_URL/api/health" >/dev/null 2>&1; then
    open_studio
    exit 0
  fi
  sleep 0.15
done

report_error "Studio did not start" "Open .studio-runtime/server.log in the repository folder for details."
exit 1
