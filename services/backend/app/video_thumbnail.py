"""从不可变视频素材提取首帧封面，缓存仅保留小尺寸 JPEG。"""
from collections import OrderedDict
import os
from pathlib import Path
import subprocess
from threading import Lock, BoundedSemaphore

from app.exporter import binary

_cache = OrderedDict()
_cache_lock = Lock()
_decoder = BoundedSemaphore(1)


def _cached(key):
    with _cache_lock:
        value = _cache.get(key)
        if value is not None:
            _cache.move_to_end(key)
        return value


def video_thumbnail(path):
    source = Path(path).resolve()
    stat = source.stat()
    key = (str(source), stat.st_mtime_ns, stat.st_size)
    cached = _cached(key)
    if cached is not None:
        return cached
    # Warm hits never wait behind decoding; recheck after admission to coalesce cold misses.
    if not _decoder.acquire(timeout=15):
        raise ValueError('视频封面解码繁忙，请稍后重试')
    try:
        cached = _cached(key)
        if cached is not None:
            return cached
        result = _thumbnail(str(source))
        with _cache_lock:
            _cache[key] = result
            while len(_cache) > 128:
                _cache.popitem(last=False)
        return result
    finally:
        _decoder.release()


def _thumbnail(path):
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    try:
        result = subprocess.run([
            binary('ffmpeg'), '-nostdin', '-v', 'error', '-threads', '1', '-i', path,
            '-map', '0:v:0', '-frames:v', '1', '-an',
            '-vf', 'scale=480:480:force_original_aspect_ratio=decrease,setsar=1',
            '-filter_threads', '1', '-c:v', 'mjpeg', '-threads', '1', '-q:v', '3', '-f', 'image2pipe', 'pipe:1',
        ], capture_output=True, timeout=15, startupinfo=startupinfo)
    except subprocess.TimeoutExpired:
        raise ValueError('视频封面提取超时') from None
    except OSError:
        raise ValueError('无法启动视频封面解码器') from None
    if result.returncode or not result.stdout:
        raise ValueError('无法提取视频封面，请检查视频是否可正常播放')
    return result.stdout
