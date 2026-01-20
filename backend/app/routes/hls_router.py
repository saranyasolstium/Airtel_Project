# app/routes/hls_router.py
from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any
import subprocess
import platform

from app.generate_mediamtx_config import generate_mediamtx_config

router = APIRouter()


class GenerateHlsBulkRequest(BaseModel):
    rtsp_urls: List[str]


def restart_mtx():
    """
    Restart MediaMTX. On Windows, kill mediamtx.exe and relaunch.
    """
    try:
        if platform.system() == "Windows":
            subprocess.run(
                ["taskkill", "/F", "/IM", "mediamtx.exe"], check=False)

            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            subprocess.Popen(
                ["mediamtx\\mediamtx.exe", "mediamtx\\mediamtx.yml"],
                startupinfo=si,
            )
        else:
            subprocess.run(["pkill", "-f", "mediamtx"], check=False)
            subprocess.Popen(
                ["./mediamtx/mediamtx", "./mediamtx/mediamtx.yml"])
    except Exception as e:
        print("Error restarting MediaMTX:", e)


@router.get("/generate-hls")
def generate_hls(
    rtsp_url: str = Query(..., description="RTSP URL"),
    background_tasks: BackgroundTasks = None,
):
    if not rtsp_url.startswith("rtsp://"):
        raise HTTPException(status_code=400, detail="Invalid RTSP URL")

    needs_restart, hls_url = generate_mediamtx_config(rtsp_url)

    if needs_restart and background_tasks is not None:
        background_tasks.add_task(restart_mtx)

    return {"hls_url": hls_url, "needs_restart": needs_restart}


@router.post("/generate-hls-bulk")
def generate_hls_bulk(
    body: GenerateHlsBulkRequest,
    background_tasks: BackgroundTasks,
):
    if not body.rtsp_urls:
        raise HTTPException(status_code=400, detail="rtsp_urls is empty")

    results: List[Dict[str, Any]] = []
    any_restart = False

    for url in body.rtsp_urls:
        if not isinstance(url, str) or not url.startswith("rtsp://"):
            results.append({"rtsp_url": url, "ok": False,
                           "error": "Invalid RTSP URL"})
            continue

        try:
            needs_restart, hls_url = generate_mediamtx_config(url)
            any_restart = any_restart or needs_restart
            results.append({"rtsp_url": url, "ok": True, "hls_url": hls_url})
        except Exception as e:
            results.append({"rtsp_url": url, "ok": False, "error": str(e)})

    if any_restart:
        background_tasks.add_task(restart_mtx)

    return {"needs_restart": any_restart, "items": results}
