"""按显示时间提取当前视频帧，不修改源素材。"""
import json
import math
from pathlib import Path
import tempfile

from app.exporter import binary, command, probe

VERSION = 'frame-extract-1'


def extract_frame(videos, config):
    if len(videos) != 1:
        raise ValueError('提取视频帧需要且只支持一个视频，请连接一个视频输出')
    time = config.get('frameTime', 0)
    if isinstance(time, bool) or not isinstance(time, (int, float)) or not math.isfinite(time) or time < 0:
        raise ValueError('截帧时间须为非负的有限秒数')
    with tempfile.TemporaryDirectory(prefix='canvas-frame-') as directory:
        source, output = Path(directory) / 'source.video', Path(directory) / 'frame.png'
        source.write_bytes(videos[0])
        info = probe(source)
        stream = next((s for s in info.get('streams', []) if s.get('codec_type') == 'video'
                       and not s.get('disposition', {}).get('attached_pic')), None)
        if stream is None:
            raise ValueError('输入素材不含视频画面，无法截帧')
        try:
            duration = float(stream.get('duration') or info.get('format', {}).get('duration'))
        except (TypeError, ValueError):
            raise ValueError('无法读取视频时长，请转换为 MP4 后重试') from None
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError('视频时长无效')
        if time > duration + .001:
            raise ValueError(f'截帧时间超出视频长度（{duration:.3f} 秒）')
        # 选择当前正在显示的帧，而不是 -ss 通常选取的下一帧；支持可变帧率和末尾定位。
        data = json.loads(command([binary('ffprobe'), '-v', 'error', '-select_streams', str(stream['index']),
                                   '-show_entries', 'frame=best_effort_timestamp_time', '-of', 'json', str(source)]))
        try:
            times = [float(frame['best_effort_timestamp_time']) for frame in data['frames']]
        except (KeyError, TypeError, ValueError):
            raise ValueError('视频缺少有效帧时间戳，无法精确截帧') from None
        if not times or any(not math.isfinite(t) for t in times) or any(b < a for a, b in zip(times, times[1:])):
            raise ValueError('视频帧时间戳无效，无法精确截帧')
        index = max((i for i, stamp in enumerate(times) if stamp - times[0] <= time + 1e-7), default=0)
        command([binary('ffmpeg'), '-nostdin', '-v', 'error', '-y', '-i', str(source),
                 '-map', f"0:{stream['index']}", '-vf', f"select=eq(n\\,{index})", '-frames:v', '1',
                 '-fps_mode', 'vfr', '-c:v', 'png', '-update', '1', str(output)])
        if not output.is_file() or not output.stat().st_size:
            raise ValueError('所选时间没有可提取的视频帧')
        return output.read_bytes()
