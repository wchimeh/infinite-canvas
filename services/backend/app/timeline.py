"""毫秒时间线校验及显式 FFmpeg 多轨滤镜规划，与画布 DAG 独立。"""
import copy
import math


def number(value, name, minimum=0, maximum=600000):
    if type(value) not in (float, int) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f'{name}必须是 {minimum}–{maximum} 之间的有限数值')
    return value


def normalize_timeline(document, allow_empty=False):
    if not isinstance(document, dict):
        raise ValueError('时间线必须是对象')
    result = copy.deepcopy(document)
    if result.get('videoEncoding', 'compatible') not in ('compatible', 'lossless'):
        raise ValueError('视频编码仅支持 Windows 兼容或无损')
    for name in ('clips', 'audio', 'subtitles'):
        result.setdefault(name, [])
        if not isinstance(result[name], list) or len(result[name]) > 500:
            raise ValueError('时间线轨道必须是数组且最多 500 个片段')
    if not result['clips'] and not allow_empty:
        raise ValueError('请先把已批准的视频加入时间线')
    for key, default in [('width', 1080), ('height', 1920)]:
        value = result.setdefault(key, default)
        if type(value) is not int or not 128 <= value <= 3840 or value % 2:
            raise ValueError('导出宽高必须是 128–3840 之间的偶数')
    if result.setdefault('fps', 30) not in (24, 25, 30):
        raise ValueError('导出帧率仅支持 24/25/30')
    cursor, total, identifiers = 0, 0, set()
    for audio, values in ((False, result['clips']), (True, result['audio'])):
        for i, value in enumerate(values):
            if not isinstance(value, dict) or not isinstance(value.get('assetId'), str):
                raise ValueError('片段缺少素材 ID')
            value.setdefault('id', ('audio-' if audio else 'clip-') + str(i))
            if not isinstance(value['id'], str) or value['id'] in identifiers:
                raise ValueError('时间线片段 ID 无效或重复')
            identifiers.add(value['id'])
            track = value.setdefault('track', 'A1' if audio else 'V1')
            if track not in (('A1', 'A2') if audio else ('V1', 'V2')):
                raise ValueError('时间线轨道类型无效')
            duration = number(value.get('durationMs'), '片段时长', 100)
            value['inMs'] = number(value.get('inMs', 0), '素材入点')
            value['startMs'] = number(value.get('startMs', 0 if audio or track == 'V2' else cursor), '时间线起点', maximum=3600000)
            value['gain'] = number(value.get('gain', 1), '音量', maximum=2)
            for fade in ('fadeInMs', 'fadeOutMs'):
                value[fade] = number(value.get(fade, 0), '淡入淡出时长', maximum=duration)
            if value['fadeInMs'] + value['fadeOutMs'] > duration:
                raise ValueError('淡入淡出不能重叠超过片段时长')
            value.setdefault('muted', False)
            if type(value['muted']) is not bool:
                raise ValueError('静音开关必须是布尔值')
            if not audio:
                if not value.get('approved'):
                    raise ValueError('视频片段尚未批准')
                transform = value.setdefault('transform', {})
                if not isinstance(transform, dict) or not transform.keys() <= {'x', 'y', 'width', 'height', 'fit', 'opacity'}:
                    raise ValueError('视频位置参数无效')
                for key in ('x', 'y'):
                    transform[key] = number(transform.get(key, 0), '画面坐标', -3840, 3840)
                for key in ('width', 'height'):
                    size = transform.get(key, result[key])
                    if type(size) is not int or not 2 <= size <= 3840 or size % 2:
                        raise ValueError('叠加画面尺寸必须是 2–3840 之间的偶数')
                    transform[key] = size
                transform['opacity'] = number(transform.get('opacity', 1), '画面透明度', maximum=1)
                if transform.setdefault('fit', 'contain') not in ('contain', 'cover'):
                    raise ValueError('画面适配仅支持 contain/cover')
                end = value['startMs'] + duration
                total = max(total, end)
                if track == 'V1':
                    cursor = max(cursor, end)
    if total > 3600000:
        raise ValueError('时间线最长支持 1 小时')
    for sub in result['subtitles']:
        if not isinstance(sub, dict) or not isinstance(sub.get('text'), str) or not sub['text'].strip():
            raise ValueError('字幕文字无效')
        start = number(sub.get('startMs'), '字幕起点', maximum=3600000)
        end = number(sub.get('endMs'), '字幕终点', maximum=3600000)
        if start >= end:
            raise ValueError('字幕终点必须晚于起点')
    result['durationMs'] = total
    return result


def seconds(milliseconds):
    return format(milliseconds / 1000, '.6f').rstrip('0').rstrip('.') or '0'


def filter_graph(timeline, video_has_audio):
    duration, fps = seconds(timeline['durationMs']), timeline['fps']
    filters = [f"color=c=black:s={timeline['width']}x{timeline['height']}:r={fps}:d={duration}[base0]",
               f'anullsrc=r=48000:cl=stereo,atrim=duration={duration}[silence]']
    labels = ['[silence]']
    ordered = sorted(enumerate(timeline['clips']), key=lambda item: (item[1]['track'], item[1]['startMs'], item[0]))
    for order, (i, clip) in enumerate(ordered):
        transform = clip['transform']
        width, height = transform['width'], transform['height']
        offset, length, start = seconds(clip['inMs']), seconds(clip['durationMs']), seconds(clip['startMs'])
        fit = f'scale={width}:{height}:force_original_aspect_ratio=increase:force_divisible_by=2:flags=lanczos,crop={width}:{height}' if transform['fit'] == 'cover' else f'scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=lanczos,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2'
        video = f'[{i}:v]trim=start={offset}:duration={length},setpts=PTS-STARTPTS,setsar=1,fps={fps},{fit}'
        # 普通片段保持 YUV，避免 RGB 往返造成额外色度采样及舍入损失。
        # 只有透明度和淡入淡出需要 alpha 通道。
        if transform['opacity'] != 1 or clip['fadeInMs'] or clip['fadeOutMs']:
            video += f',format=rgba,colorchannelmixer=aa={transform["opacity"]}' if transform['opacity'] != 1 else ',format=yuva420p'
        if clip['fadeInMs']:
            video += f",fade=t=in:st=0:d={seconds(clip['fadeInMs'])}:alpha=1"
        if clip['fadeOutMs']:
            video += f",fade=t=out:st={seconds(clip['durationMs'] - clip['fadeOutMs'])}:d={seconds(clip['fadeOutMs'])}:alpha=1"
        filters.append(video + f',setpts=PTS+{start}/TB[v{i}]')
        end = seconds(clip['startMs'] + clip['durationMs'])
        filters.append(f"[base{order}][v{i}]overlay=x={transform['x']}:y={transform['y']}:eof_action=pass:repeatlast=0:enable='gte(t,{start})*lt(t,{end})'[base{order + 1}]")
    filters.append(f"[base{len(ordered)}]format=yuv420p[video]")
    for i, clip in enumerate([*timeline['clips'], *timeline['audio']]):
        if clip['muted'] or (i < len(video_has_audio) and not video_has_audio[i]):
            continue
        audio = f"[{i}:a]atrim=start={seconds(clip['inMs'])}:duration={seconds(clip['durationMs'])},asetpts=PTS-STARTPTS,aresample=48000,volume={clip['gain']}"
        if clip['fadeInMs']:
            audio += f",afade=t=in:st=0:d={seconds(clip['fadeInMs'])}"
        if clip['fadeOutMs']:
            audio += f",afade=t=out:st={seconds(clip['durationMs'] - clip['fadeOutMs'])}:d={seconds(clip['fadeOutMs'])}"
        delay = round(clip['startMs'])
        filters.append(audio + f',adelay={delay}|{delay}[a{i}]')
        labels.append(f'[a{i}]')
    filters.append(''.join(labels) + f'amix=inputs={len(labels)}:duration=first:normalize=0,alimiter=limit=0.95:level=0:latency=1[audio]')
    return ';'.join(filters)
