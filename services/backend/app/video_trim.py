"""本地精确截取视频时间段，保留首条可用音轨。"""
import math
from pathlib import Path
import tempfile

from app.exporter import binary, command, probe

VERSION = 'video-trim-1'


def trim_video(videos, config):
    if len(videos) != 1:
        raise ValueError('视频裁剪需要且只支持一个视频，请连接一个视频输出')
    start, end = config.get('trimStart', 0), config.get('trimEnd')
    for value in [start, *([] if end is None else [end])]:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError('裁剪时间须为非负的有限秒数')
    if end is not None and end <= start:
        raise ValueError('结束时间必须大于开始时间')
    with tempfile.TemporaryDirectory(prefix='canvas-video-trim-') as directory:
        source, output = Path(directory) / 'source.video', Path(directory) / 'trim.mp4'
        source.write_bytes(videos[0])
        info = probe(source)
        video = next((stream for stream in info.get('streams', []) if stream.get('codec_type') == 'video' and not stream.get('disposition', {}).get('attached_pic')), None)
        if video is None:
            raise ValueError('输入素材不含视频画面，无法裁剪')
        try:
            duration = float(video.get('duration') or info.get('format', {}).get('duration'))
        except (TypeError, ValueError) as exc:
            raise ValueError('无法读取视频时长，请转换为 MP4 后重试') from exc
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError('视频时长无效')
        if start >= duration or (end is not None and end > duration + 0.001):
            raise ValueError(f'裁剪时间超出视频长度（{duration:.3f} 秒）')
        end = min(end, duration) if end is not None else duration
        command([binary('ffmpeg'), '-nostdin', '-v', 'error', '-y', '-i', str(source),
                 '-ss', str(start), '-t', str(end - start), '-map', '0:V:0', '-map', '0:a:0?',
                 '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
                 '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(output)])
        result = probe(output)
        if not any(s.get('codec_type') == 'video' for s in result.get('streams', [])):
            raise ValueError('所选时间段未输出有效视频，请至少保留一帧')
        return output.read_bytes()
