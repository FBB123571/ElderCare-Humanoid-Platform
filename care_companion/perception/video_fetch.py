"""下载或读取网络/本地视频，供分析管线使用。"""
from __future__ import annotations

import logging
import shutil
import tempfile
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_BYTES = 80 * 1024 * 1024  # 80MB


def _urlopen_no_proxy(req: urllib.request.Request, timeout: int = 120):
  opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
  return opener.open(req, timeout=timeout)


def fetch_video_to_path(url: str, dest: Path) -> Path:
  """将 url 下载到 dest（支持 http/https 直链）。"""
  dest = Path(dest)
  dest.parent.mkdir(parents=True, exist_ok=True)
  req = urllib.request.Request(url, headers={"User-Agent": "CareCompanion/1.0"})
  with _urlopen_no_proxy(req, timeout=180) as resp:
    clen = resp.headers.get("Content-Length")
    if clen and int(clen) > MAX_BYTES:
      raise ValueError(f"视频过大 (>{MAX_BYTES // (1024*1024)}MB)，请换更短片段")
    total = 0
    with open(dest, "wb") as f:
      while True:
        chunk = resp.read(1024 * 256)
        if not chunk:
          break
        total += len(chunk)
        if total > MAX_BYTES:
          raise ValueError("视频超过大小限制")
        f.write(chunk)
  if dest.stat().st_size < 1024:
    dest.unlink(missing_ok=True)
    raise ValueError("下载失败或文件过小")
  return dest


def save_upload_to_temp(data: bytes, suffix: str = ".mp4") -> Path:
  if len(data) > MAX_BYTES:
    raise ValueError("上传视频超过大小限制")
  fd, name = tempfile.mkstemp(suffix=suffix)
  path = Path(name)
  import os

  with os.fdopen(fd, "wb") as f:
    f.write(data)
  return path


def resolve_video_source(url: str | None = None, upload_bytes: bytes | None = None) -> tuple[Path, str]:
  """返回 (本地路径, 来源标签)。"""
  if upload_bytes:
    return save_upload_to_temp(upload_bytes), "upload"
  if not url or not url.strip():
    raise ValueError("请提供视频 URL 或上传文件")
  url = url.strip()
  tmp = Path(tempfile.mkstemp(suffix=".mp4")[1])
  try:
    fetch_video_to_path(url, tmp)
    return tmp, "url"
  except Exception as exc:
    tmp.unlink(missing_ok=True)
    raise ValueError(f"无法获取视频: {exc}") from exc


def cleanup_path(path: Path | None) -> None:
  if path and path.exists():
    try:
      path.unlink()
    except OSError:
      logger.debug("cleanup skip %s", path)
