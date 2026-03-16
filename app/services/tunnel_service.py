"""Public share link via Cloudflare Quick Tunnels or localtunnel."""
import re
import secrets
import subprocess
import threading
from typing import Optional

from app.core.config import settings

# Cloudflare prints "Your quick Tunnel has been created! Visit it at: https://xxx.trycloudflare.com"
TRYCLOUDFLARE_RE = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")


class TunnelService:
    """Start/stop tunnel process and track share URL."""

    def __init__(self) -> None:
        self._process: Optional[subprocess.Popen] = None
        self._share_url: Optional[str] = None
        self._error: Optional[str] = None
        self._reader_thread: Optional[threading.Thread] = None

    @property
    def share_url(self) -> Optional[str]:
        return self._share_url

    @property
    def error(self) -> Optional[str]:
        return self._error

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def _read_stdout(self) -> None:
        if not self._process or not self._process.stdout:
            return
        for line in iter(self._process.stdout.readline, ""):
            if not line:
                break
            match = TRYCLOUDFLARE_RE.search(line)
            if match:
                self._share_url = match.group(0)
                break
            # localtunnel: "your url is: https://xxx.loca.lt"
            if "loca.lt" in line or "localtunnel.me" in line:
                for part in line.split():
                    if part.startswith("http"):
                        self._share_url = part.strip(" \n\r")
                        break

    def start(self, local_url: str = "http://127.0.0.1:8000") -> bool:
        if self.is_running:
            return True
        self._error = None
        self._share_url = None
        try:
            if settings.tunnel_type == "cloudflare":
                self._process = subprocess.Popen(
                    [settings.cloudflared_path, "tunnel", "--url", local_url],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                self._reader_thread = threading.Thread(target=self._read_stdout, daemon=True)
                self._reader_thread.start()
            else:
                self._process = subprocess.Popen(
                    [settings.localtunnel_path, "--port", "8000"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                self._reader_thread = threading.Thread(target=self._read_stdout, daemon=True)
                self._reader_thread.start()
            return True
        except FileNotFoundError as e:
            self._error = f"Tunnel binary not found: {e}"
            return False
        except Exception as e:
            self._error = str(e)
            return False

    def stop(self) -> None:
        if self._process and self._process.poll() is None:
            self._process.terminate()
            self._process.wait(timeout=5)
        self._process = None
        self._share_url = None
        self._reader_thread = None


tunnel_service = TunnelService()


def generate_share_token() -> str:
    return secrets.token_urlsafe(16)
