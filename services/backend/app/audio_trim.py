"""本地按时间区间裁剪音频，保留原始素材。"""
import math
from pathlib import Path
import tempfile

from app.exporter import binary, command, probe

VERSION = 'audio-trim-1'


def trim_audio(audios, config):
    if len(audios) != 1:
        raise ValueError('音频裁剪需要且只支持一个音频，请连接一个音频输出')
    start, end = config.get('trimStart', 0), config.get('trimEnd')
    for value in [start, *([] if end is None else [end])]:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError('裁剪时间须为非负的有限秒数')
    if end is not None and end <= start:
        raise ValueError('结束时间必须大于开始时间')
    with tempfile.TemporaryDirectory(prefix='canvas-trim-') as directory:
        source, output = Path(directory) / 'source.audio', Path(directory) / 'trim.wav'
        source.write_bytes(audios[0])
        info = probe(source)
        audio = next((stream for stream in info.get('streams', []) if stream.get('codec_type') == 'audio'), None)
        if audio is None:
            raise ValueError('输入素材不含音轨，无法裁剪')
        try:
            duration = float(audio.get('duration') or info.get('format', {}).get('duration'))
        except (ValueError, TypeError) as exc:
            raise ValueError('无法读取音频时长，请转换为 WAV 后重试') from exc
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError('音频时长无效')
        if start >= duration or (end is not None and end > duration + 0.001):
            raise ValueError(f'裁剪时间超出音频长度（{duration:.3f} 秒）')
        end = min(end, duration) if end is not None else duration
        command([binary('ffmpeg'), '-nostdin', '-v', 'error', '-y', '-i', str(source),
                 '-map', '0:a:0', '-vn', '-af', f'atrim=start={start}:end={end},asetpts=PTS-STARTPTS',
                 '-c:a', 'pcm_s16le', str(output)])
        if output.stat().st_size <= 44:
            raise ValueError('所选时间段未输出有效音频')
        return output.read_bytes()
