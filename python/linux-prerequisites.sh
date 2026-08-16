#!/bin/bash

set -euo pipefail

# python-rtmidi talks to the MIDI Commander over USB. It ships prebuilt wheels
# only for some Python versions; on anything newer it is compiled from source,
# which needs the ALSA development headers. JACK is optional — rtmidi builds
# without it, just without a JACK backend.
#
# Use libjack-jackd2-dev, NOT libjack-dev. The latter is JACK1, and installing
# it makes apt remove the JACK2 runtime (libjack-jackd2-0) that a modern
# desktop audio stack depends on.
sudo apt install -y libasound2-dev libjack-jackd2-dev

# Debian and Ubuntu mark the system interpreter as externally managed (PEP 668),
# so pip refuses to install into it — with or without sudo. Install into a
# virtual environment beside this script instead.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"

python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install -r "$SCRIPT_DIR/requirements.txt"

cat <<EOF

Done. Run the configuration tool with:

  $VENV/bin/python $SCRIPT_DIR/CSV_to_Flash.py <config.csv>

Or activate the environment first:

  source $VENV/bin/activate
EOF
