"""WiFi configuration (scan, connect). Requires nmcli or platform helpers on the device."""
import subprocess
from typing import List

from fastapi import APIRouter, HTTPException

from app.models.settings import WifiNetwork, WifiConfig

router = APIRouter()


def _has_nmcli() -> bool:
    try:
        subprocess.run(["which", "nmcli"], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


@router.get("/wifi/scan", response_model=List[WifiNetwork])
def wifi_scan() -> List[WifiNetwork]:
    """Scan for WiFi networks. Uses nmcli on Linux."""
    if not _has_nmcli():
        return []
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return []
        networks: List[WifiNetwork] = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split(":")
            ssid = parts[0] if len(parts) > 0 else ""
            signal = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            security = (parts[2] if len(parts) > 2 else "").lower()
            if ssid:
                networks.append(
                    WifiNetwork(
                        ssid=ssid,
                        signal_strength=signal,
                        secured="wpa" in security or "wep" in security,
                        connected=False,
                    )
                )
        return networks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wifi/connect")
def wifi_connect(config: WifiConfig) -> dict:
    """Connect to WiFi. Uses nmcli; may require root or NetworkManager."""
    if not _has_nmcli():
        raise HTTPException(status_code=501, detail="nmcli not available")
    try:
        cmd = [
            "nmcli", "device", "wifi", "connect", config.ssid,
        ]
        if config.password:
            cmd.extend(["password", config.password])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail=result.stderr or "Connection failed",
            )
        return {"success": True, "message": result.stdout or "Connected"}
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Connection timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
