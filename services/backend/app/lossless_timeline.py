"""自动匹配原片画幅：统一尺寸等比例缩放，保留原帧率及色彩格式。"""
import copy
from fractions import Fraction


def preserve_source_timeline(timeline, streams):
    def composition_error():
        raise ValueError('原片尺寸模式仅支持顺序剪辑；当前存在画面编辑，请选择「按时间线合成」')

    if timeline['subtitles']:
        composition_error()
    cursor = 0
    for clip in timeline['clips']:
        transform = clip['transform']
        if (clip['track'] != 'V1' or abs(clip['startMs'] - cursor) > 0.001
                or clip['fadeInMs'] or clip['fadeOutMs']
                or transform.get('opacity', 1) != 1
                or transform.get('x', 0) or transform.get('y', 0)
                or transform.get('width') != timeline['width']
                or transform.get('height') != timeline['height']):
            composition_error()
        cursor += clip['durationMs']

    rates = []
    for stream in streams:
        if (stream.get('pix_fmt') != 'yuv420p'
                or stream.get('color_range', 'tv') not in ('tv', 'unknown')
                or stream.get('color_transfer') in ('smpte2084', 'arib-std-b67')):
            raise ValueError('原片画质模式暂不支持此位深、色度或 HDR 格式，已停止导出以避免转换损失')
        if any(type(stream.get(key)) is not int or not 2 <= stream[key] <= 8192 or stream[key] % 2
               for key in ('width', 'height')):
            raise ValueError('原片尺寸需要是 2–8192 之间的偶数，无法保证当前素材无损布局')
        if stream.get('sample_aspect_ratio', '1:1') not in ('1:1', 'N/A') or any(
                entry.get('rotation', 0) for entry in stream.get('side_data_list', [])):
            raise ValueError('原片带有旋转或非方形像素，暂不支持严格原片导出')
        try:
            rate = Fraction(stream.get('avg_frame_rate', '0/1'))
            nominal = Fraction(stream.get('r_frame_rate', '0/1'))
        except (ValueError, ZeroDivisionError):
            raise ValueError('无法识别原片帧率，已停止导出以避免丢帧') from None
        if rate.denominator != 1 or not 1 <= rate <= 120 or rate != nominal:
            raise ValueError('原片画质模式暂只支持相同整数恒定帧率（1–120 fps），不会自动转换帧率')
        rates.append(int(rate))
    if len(set(rates)) != 1:
        raise ValueError('原片帧率不同，无法保证拼接后逐帧不变；请使用相同帧率片段')
    for field in ('color_space', 'color_transfer', 'color_primaries'):
        if len({s.get(field, 'unknown') for s in streams}) != 1:
            raise ValueError('原片色彩标记不同，无法在同一成片中无损保留，请先统一素材')

    result = copy.deepcopy(timeline)
    result['width'] = max(s['width'] for s in streams)
    result['height'] = max(s['height'] for s in streams)
    result['fps'] = rates[0]
    for clip in result['clips']:
        # 同比例片段直接填满；不同比例通过 contain 仅保留必要留边。
        clip['transform'] = {'width': result['width'], 'height': result['height'],
                             'x': 0, 'y': 0,
                             'fit': 'contain', 'opacity': 1}
    return result
