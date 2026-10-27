"""本地提取视频的第一条音轨，不修改原始素材。"""
from pathlib import Path
import tempfile

from app.exporter import binary, command, probe


VERSION = 'audio-extract-1'


def extract_audio(videos):
    if len(videos) != 1:
        raise ValueError('提取视频音频需要且只支持一个视频，请连接一个视频输出')
    with tempfile.TemporaryDirectory(prefix='canvas-audio-') as directory:
        source = Path(directory) / 'source.video'
        output = Path(directory) / 'audio.wav'
        source.write_bytes(videos[0])
        streams = probe(source).get('streams', [])
        if not any(stream.get('codec_type') == 'video' for stream in streams):
            raise ValueError('输入素材没有视频画面，请连接视频素材')
        if not any(stream.get('codec_type') == 'audio' for stream in streams):
            raise ValueError('该视频不含音轨，无法提取音频')
        command([binary('ffmpeg'), '-nostdin', '-v', 'error', '-y', '-i', str(source),
                 '-map', '0:a:0', '-vn', '-c:a', 'pcm_s16le', str(output)])
        return output.read_bytes()
