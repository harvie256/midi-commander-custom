# Packaging options for MIDI Commander Studio

Status: **exploratory**. Nothing here is committed to. This records two candidate
directions so the reasoning does not have to be rediscovered later.

## The problem

Studio is a local FastAPI server that the user reaches through a browser. That is
a developer-normal idiom and a user-strange one, but the browser window is the
*least* of the friction. Before a non-technical user sees a tab, they must:

| Platform | What we currently ask of them |
| --- | --- |
| Windows | Download the repo as a ZIP and extract it; install Python from python.org remembering to tick *Add to PATH*; double-click a `.cmd` that shells into `powershell -ExecutionPolicy Bypass`; wait through a pip install. Then run Zadig and rebind a USB driver to flash firmware. |
| macOS | Same ZIP dance; `python3` triggers the Xcode Command Line Tools prompt (multi-GB); the `.command` file hits Gatekeeper's "unidentified developer" wall, needing the right-click→Open trick; `install_dfu_util` shells out to **Homebrew**, which such a user does not have. |
| Linux | A C++ toolchain and ALSA headers, because `python-rtmidi` has no wheel for newer Pythons (none for 3.14, which Ubuntu 26.04 ships). |

So the goal is not "replace the browser window". It is **stop asking users to
assemble a development environment**. Any option is judged mainly on how much of
the table above it deletes.

## What already changed

Removing the CSV path (see [CLAUDE.md](CLAUDE.md#the-removed-csv-path)) was the
prerequisite for everything below, and it is done.

The flash encoder used to be two `pandas`-coupled modules shaped around CSV rows,
shared with a CLI. Porting that to another language would have been miserable and
would have forked a binary format nothing validates. It is now
`studio/backend/flash_packer.py` — **192 lines of dependency-free byte packing**
that walks the typed model directly, with its constants pinned against the
firmware headers by tests. Porting *that* is an afternoon in any language.

That is what puts both options below on the table.

## Current shape, by what it would cost to move

```
studio/backend/               1087 lines total
  flash_packer.py     192  pure logic — trivially portable
  config_service.py   124  pure logic — trivially portable
  models.py           105  schema, already mirrored in types.ts
  app.py              159  HTTP plumbing — disappears in both options
  jobs.py              63  async job store — disappears in both options
  device_service.py   443  hardware: MIDI + DFU. The real work.
studio/frontend/src/  1143  survives nearly intact in both options
Launch/Stop scripts    292  disappears in both options
```

Roughly 380 lines are pure logic, ~220 lines exist only because there is a
server, and `device_service.py` is the part that actually touches hardware —
and about 90 lines of *that* is `dfu-util` bootstrap (the pinned Windows
download, the Homebrew call) which is itself a symptom of not shipping an app.

Note also that project state already lives in `localStorage`, not on the server,
and every endpoint takes the full `StudioProject` in the request body. Studio is
already architected like a client-side app that happens to be wearing a server.

---

## Option B — Tauri desktop app

Rust core with the OS webview (WebView2 / WKWebView / WebKitGTK), producing
signable `.msi` / `.dmg` / `.AppImage` at roughly 10 MB.

**What survives:** the entire React frontend. `api.ts` swaps `fetch()` for
Tauri's `invoke()`; components are untouched.

**What gets ported to Rust:**

- `flash_packer.py` → straightforward struct packing
- `config_service.py` → straightforward validation
- MIDI I/O → [`midir`](https://crates.io/crates/midir), which supports SysEx
- DFU → either keep shelling out to `dfu-util`, or use a libusb crate directly
  and drop the external binary entirely

**What disappears outright:** Python, pip, venvs, the compile-from-source
`python-rtmidi` problem, Homebrew, FastAPI, uvicorn, the localhost server, the
job store and its 500 ms polling (Tauri events replace it), `/api/shutdown`, and
all 292 lines of launcher script.

**Costs and risks**

- Rust becomes a maintenance skill requirement for the project.
- `python-rtmidi` → `midir` is a real behavioural port; MIDI backends have
  platform quirks and this is the code path with no test coverage today.
- Backend test coverage restarts at zero. The 34 existing tests do not port.
- **Code signing is unavoidable** to get the benefit — see below.

**Open questions**

- Bundle `dfu-util` or reimplement DFU in Rust? Bundling raises redistribution
  questions (`dfu-util` is GPLv2); reimplementing is more work but yields one
  self-contained binary with no external process.
- Does the firmware `.dfu` ship inside the bundle, or keep the current
  "prefer a local build, fall back to the committed file" resolution?

---

## Option C — Static web app, no install at all

Publish the frontend as a static site (GitHub Pages). No server, no download, no
packaging. The pedal is reached directly from the page.

- **Config upload** → Web MIDI API, which supports SysEx
- **Firmware flashing** → WebUSB plus a DFU implementation

**What survives:** the React app, again nearly intact.

**What gets ported to TypeScript:** `flash_packer.py` and `config_service.py` —
about 320 lines of pure logic with no dependencies. `device_service.py`'s MIDI
and DFU halves become browser API calls.

**What disappears outright:** everything Option B removes, *plus the entire
distribution problem* — no release artifacts, no installers, no code signing, no
notarization, no per-OS anything. Users visit a URL.

**Costs and risks**

- **Chromium only.** Web MIDI with SysEx and WebUSB are supported in
  Chrome/Edge/Opera. Safari supports neither. Firefox's Web MIDI support is
  partial and its SysEx story is awkward. *Verify current browser support before
  committing — this changes over time.*
- Both APIs require a secure context (HTTPS or localhost) and a user permission
  prompt.
- Windows **still** needs the WinUSB driver rebind for the DFU half.
- Some users are wary of a web page touching hardware, however local it is.
- Loses the ability to read/write the user's filesystem freely — though the
  current app only does file open/save, which the browser already handles.

**Open questions**

- Where does the firmware `.dfu` come from — bundled as a fetched asset, or
  user-supplied?
- Is a published web page an acceptable home for a firmware flasher, or should
  flashing stay local?

---

## Side by side

| | B — Tauri app | C — Static web app |
| --- | --- | --- |
| User installs | One signed binary | Nothing — visit a URL |
| Removes the whole dependency table | Yes | Yes |
| Removes the distribution problem | No — creates it | Yes |
| Code signing needed | Yes, recurring cost | No |
| Browser constraints | None | Chromium only |
| Frontend reuse | Near total | Near total |
| Logic to port | ~380 lines → Rust | ~380 lines → TypeScript |
| Hardware work | `midir` + DFU | Web MIDI + WebUSB |
| New maintenance skill | Rust | None |
| Existing backend tests | Lost | Lost |

## What neither option fixes

- **The Windows DFU driver.** Zadig and the WinUSB rebind is the ugliest step in
  the product and is inherent to reaching the STM32 bootloader via libusb.
  Fixing it properly means a signed driver package — a deeper rabbit hole than
  the app itself.
- **Linux DFU permissions.** Still needs root or a udev rule for `0483:df11`.
- **Code signing (Option B only).** An unsigned Windows binary triggers a
  SmartScreen warning that arguably looks *worse* than the current script; a
  certificate is a few hundred dollars a year and OV certs need reputation
  before the warning stops. macOS notarization needs a $99/yr Apple Developer
  account, or users are back to right-click→Open — having done all that work
  precisely to avoid it. For a free hobby project this is a real recurring
  personal cost, and it should be decided **before** the packaging work, not
  after.

## A hybrid worth considering

Flashing firmware happens essentially once per user. Editing and uploading
configurations is the recurring activity. That asymmetry argues for matching
install cost to usage frequency:

- **Static web app** for the editor and config upload — the 95% case, zero
  install, and it sidesteps code signing entirely.
- **Firmware flashing** stays a documented `dfu-util` command, or a small
  separate download for the rare occasion.

This gets most of Option C's benefit without betting the scary, once-per-user
operation on WebUSB.

## If picking one up

**Option B:** prototype `flash_packer` in Rust first and check it against
`studio/backend/tests/fixtures/rc600_reference.json` — that golden image is
language-agnostic and will tell you immediately whether the port is correct.
Then prove `midir` can complete a SysEx upload before committing to the rest.

**Option C:** same golden-image check for the TypeScript port, then verify Web
MIDI SysEx round-trips with the pedal on your target browsers. The
[config transfer protocol](CLAUDE.md#config-transfer-protocol-usb-sysex) is
small — erase, chunked write, reset, each awaiting its reply.

Either way the golden image is the cheap early signal: if the ported encoder
reproduces those 2688 bytes, the hardest-to-debug part is already correct.
