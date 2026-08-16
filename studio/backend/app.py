from __future__ import annotations

import argparse
import os
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config_service import pack_project, project_stats, validate_project
from .device_service import (
    firmware_status,
    install_dfu_util,
    install_firmware,
    scan_midi_devices,
    test_command,
    upload_configuration,
)
from .jobs import JobStore
from .models import (
    FirmwareInstallRequest,
    StudioProject,
    TestCommandRequest,
    UploadRequest,
    starter_project,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = REPO_ROOT / "studio" / "frontend" / "dist"
jobs = JobStore()
app = FastAPI(title="MIDI Commander Studio", docs_url="/api/docs")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/project/starter")
def get_starter_project() -> StudioProject:
    return starter_project()


@app.post("/api/project/validate")
def validate(project: StudioProject) -> dict[str, object]:
    issues = validate_project(project)
    has_errors = any(issue["level"] == "error" for issue in issues)
    stats = (
        project_stats(project)
        if not has_errors
        else {
            "contentSize": 0,
            "commandCount": sum(
                len(button.commands) for bank in project.banks for button in bank.buttons
            ),
        }
    )
    return {"issues": issues, "stats": stats}


@app.post("/api/project/pack")
def pack(project: StudioProject) -> dict[str, int]:
    try:
        packed = pack_project(project)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"bytes": len(packed), "chunks": len(packed) // 16}


@app.get("/api/devices")
def devices() -> dict[str, object]:
    return scan_midi_devices()


@app.post("/api/commands/test")
def send_test_command(request: TestCommandRequest) -> dict[str, bool]:
    try:
        test_command(request.outputName, request.command)
    except Exception as exc:  # noqa: BLE001 - hardware errors belong in UI
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"sent": True}


@app.post("/api/upload/start")
def start_upload(request: UploadRequest) -> dict[str, str]:
    issues = validate_project(request.project)
    errors = [issue for issue in issues if issue["level"] == "error"]
    if errors:
        raise HTTPException(status_code=400, detail=errors[0]["message"])
    job = jobs.start(
        "configuration-upload",
        lambda current: upload_configuration(
            request.project, request.inputName, request.outputName, current
        ),
    )
    return {"jobId": job.id}


@app.get("/api/firmware/status")
def get_firmware_status() -> dict[str, object]:
    return firmware_status()


@app.post("/api/firmware/install-dfu-util")
def start_dfu_install() -> dict[str, str]:
    job = jobs.start("dependency-install", install_dfu_util)
    return {"jobId": job.id}


@app.post("/api/firmware/install")
def start_firmware_install(request: FirmwareInstallRequest) -> dict[str, str]:
    if not request.recoveryConfirmed:
        raise HTTPException(status_code=400, detail="Confirm that you have a stock recovery file.")
    job = jobs.start("firmware-install", lambda current: install_firmware(current, request.source))
    return {"jobId": job.id}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, object]:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job.as_dict()


@app.post("/api/shutdown")
def shutdown() -> dict[str, bool]:
    threading.Timer(0.4, lambda: os._exit(0)).start()
    return {"stopping": True}


if FRONTEND_DIST.exists():
    assets = FRONTEND_DIST / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str) -> FileResponse:
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MIDI Commander Studio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
