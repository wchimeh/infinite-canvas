"""不可变源素材的多轨合成、低分辨率预览与可校验 MP4 导出。"""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from app.timeline import normalize_timeline, filter_graph, seconds


def binary(name):
    directory = os.getenv('FFMPEG_DIR', '')
    candidate = Path(directory) / (name + ('.exe' if os.name == 'nt' else '')) if directory else None
    path = str(candidate) if candidate and candidate.is_file() else shutil.which(name)
    if not path:
        raise ValueError(f'未找到 {name}，请安装 FFmpeg 并配置 FFMPEG_DIR 后重试')
    return path


def command(args, cwd=None):
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=900, startupinfo=startupinfo)
    if result.returncode:
        raise ValueError('媒体处理失败：' + result.stderr[-1500:])
    return result.stdout


def probe(path):
    return json.loads(command([binary('ffprobe'), '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))


def validate_timeline(store, pid, timeline):
    try:
        normalized = normalize_timeline(timeline)
    except (ValueError, TypeError, KeyError) as exc:
        return [str(exc)]
    errors = []
    for audio, values in ((False, normalized['clips']), (True, normalized['audio'])):
        for clip in values:
            try:
                asset = store.asset(clip['assetId'])
                if asset['projectId'] != pid:
                    raise ValueError('素材不属于当前项目')
                store.asset_path(asset['id'])
                if not asset['mime'].startswith('audio/' if audio else 'video/'):
                    raise ValueError('音频轨只接受音频素材' if audio else '视频轨只接受视频素材')
            except (ValueError, KeyError, TypeError) as exc:
                errors.append(str(exc))
    return errors


def timecode(ms):
    value = int(ms)
    return f'{value // 3600000:02d}:{value // 60000 % 60:02d}:{value // 1000 % 60:02d},{value % 1000:03d}'


def preview_timeline(timeline):
    result = copy.deepcopy(timeline)
    factor = min(1, max(128 / min(result['width'], result['height']), 720 / max(result['width'], result['height'])))
    for key in ('width', 'height'):
        result[key] = max(128, round(result[key] * factor / 2) * 2)
    for clip in result['clips']:
        transform = clip['transform']
        for key in ('x', 'y'):
            transform[key] = round(transform[key] * factor)
        for key in ('width', 'height'):
            transform[key] = max(2, round(transform[key] * factor / 2) * 2)
    return result


def export_timeline(store, pid, timeline, job_id, preview=False):
    errors = validate_timeline(store, pid, timeline)
    if errors:
        raise ValueError('；'.join(errors))
    normalized = normalize_timeline(timeline)
    render = preview_timeline(normalized) if preview else normalized
    ffmpeg = binary('ffmpeg')
    directory = store.project_dir(pid) / 'exports'
    if not isinstance(job_id, str) or not job_id or Path(job_id).name != job_id or any(c in job_id for c in ('/', '\\', ':', '\x00')):
        raise ValueError('导出标识无效')
    target = directory / (job_id + '.mp4')
    partial = target.with_suffix('.partial.mp4')
    assets, has_audio = [], []
    for i, clip in enumerate([*render['clips'], *render['audio']]):
        source = store.asset_path(clip['assetId'])
        info = probe(source)
        available = float(info['format'].get('duration', 0)) * 1000
        if available + 1000 / render['fps'] < clip['inMs'] + clip['durationMs']:
            raise ValueError(f'第 {i + 1} 个素材短于设定裁切范围，请缩短时长或调整入点')
        streams = info.get('streams', [])
        is_video = i < len(render['clips'])
        if not any(s['codec_type'] == ('video' if is_video else 'audio') for s in streams):
            raise ValueError('素材实际媒体轨道与时间线类型不匹配')
        assets.append(source)
        if is_video:
            has_audio.append(any(s['codec_type'] == 'audio' for s in streams))
    with tempfile.TemporaryDirectory(prefix='render-', dir=directory) as tmp:
        temp = Path(tmp)
        graph = filter_graph(render, has_audio)
        subtitles = render['subtitles']
        video_label = '[video]'
        if subtitles:
            srt = '\n\n'.join(f"{i}\n{timecode(s['startMs'])} --> {timecode(s['endMs'])}\n{s['text'].replace(chr(13), '').replace(chr(0), '')}" for i, s in enumerate(subtitles, 1)) + '\n'
            (temp / 'subtitles.srt').write_text(srt, encoding='utf-8')
            graph += ";[video]subtitles=subtitles.srt:force_style='FontName=Microsoft YaHei,FontSize=18,MarginV=28'[subvideo]"
            video_label = '[subvideo]'
        args = [ffmpeg, '-y', '-v', 'error']
        for source in assets:
            args += ['-threads', '2', '-i', str(source)]
        args += ['-filter_complex_threads', '1', '-filter_complex', graph, '-map', video_label, '-map', '[audio]',
                 '-c:v', 'libx264', '-threads', '2', '-preset', 'ultrafast' if preview else 'fast', '-crf', '28' if preview else '20',
                 '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ar', '48000', '-ac', '2', '-t', seconds(render['durationMs']),
                 '-movflags', '+faststart', str(partial)]
        try:
            command(args, temp)
            result = probe(partial)
            video = next(s for s in result['streams'] if s['codec_type'] == 'video')
            if video['width'] != render['width'] or video['height'] != render['height'] or not any(s['codec_type'] == 'audio' for s in result['streams']):
                raise ValueError('导出媒体轨道校验失败')
            if abs(float(result['format']['duration']) - render['durationMs'] / 1000) > 1 / render['fps']:
                raise ValueError('导出时长与时间线不一致（超过一帧）')
            os.replace(partial, target)
            if subtitles:
                shutil.copyfile(temp / 'subtitles.srt', target.with_suffix('.srt'))
        finally:
            partial.unlink(missing_ok=True)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest = {'timeline': normalized, 'render': render, 'preview': preview, 'sha256': digest,
                'ffmpeg': command([ffmpeg, '-version']).splitlines()[0], 'createdAt': time.time(), 'durationMs': render['durationMs']}
    target.with_suffix('.manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'path': str(target.relative_to(store.project_dir(pid))), 'durationMs': render['durationMs'], 'sha256': digest, 'preview': preview}
