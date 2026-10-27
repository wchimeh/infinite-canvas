"""Convert local reference media into compatible multimodal content parts."""
import base64
import math
from pathlib import Path
import tempfile

from app.exporter import binary, command, probe

MAX_BYTES = 20 * 1024 * 1024


def media_content(audios, videos):
    parts = []
    for kind, items in [('audio', audios), ('video', videos)]:
        if len(items) > 3:
            raise ValueError('扩写最多支持 3 段参考音频和 3 段参考视频')
        for index, data in enumerate(items):
            if not isinstance(data, bytes) or not data or len(data) > MAX_BYTES:
                raise ValueError('参考音视频为空或超过 20 MiB，请先裁剪或压缩')
            with tempfile.TemporaryDirectory(prefix='canvas-reference-') as directory:
                source = Path(directory) / 'source.media'
                output = Path(directory) / ('audio.wav' if kind == 'audio' else 'video.mp4')
                source.write_bytes(data)
                info = probe(source)
                if not any(s.get('codec_type') == kind and not s.get('disposition', {}).get('attached_pic') for s in info.get('streams', [])):
                    raise ValueError('参考媒体类型不匹配或缺少有效音视频轨道')
                try:
                    duration = float(info.get('format', {}).get('duration'))
                except (ValueError, TypeError) as exc:
                    raise ValueError('无法读取参考媒体时长，请重新导入有效音视频') from exc
                if not math.isfinite(duration) or not 0 < duration <= 120:
                    raise ValueError('参考音视频须在 120 秒以内，请先使用裁剪节点')
                args = [binary('ffmpeg'), '-nostdin', '-v', 'error', '-y', '-i', str(source)]
                if kind == 'audio':
                    args += ['-map', '0:a:0', '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le']
                else:
                    args += ['-map', '0:V:0', '-an', '-vf', 'scale=720:720:force_original_aspect_ratio=decrease:force_divisible_by=2',
                             '-c:v', 'libx264', '-preset', 'fast', '-crf', '25', '-pix_fmt', 'yuv420p', '-movflags', '+faststart']
                command([*args, str(output)])
                if output.stat().st_size > MAX_BYTES:
                    raise ValueError('转换后的参考媒体超过 20 MiB，请先裁剪较短片段')
                encoded = base64.b64encode(output.read_bytes()).decode('ascii')
            parts.append({'type': 'text', 'text': f'<{kind.title()} {index + 1}> (reference {kind} {index + 1})'})
            if kind == 'audio':
                parts.append({'type': 'input_audio', 'input_audio': {'data': 'data:audio/wav;base64,' + encoded, 'format': 'wav'}})
            else:
                parts.append({'type': 'video_url', 'video_url': {'url': 'data:video/mp4;base64,' + encoded}})
    return parts
