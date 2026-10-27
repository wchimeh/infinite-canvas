# -*- coding: utf-8 -*-
# @File:     process_generate.py
# @Author:
# @DateTime: 2025/06/10/17:04
import os
import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import random
import time
try:
    from .rh_process_generate import process_generate as _process_generate
except ImportError:  # 兼容原脚本直接执行
    from rh_process_generate import process_generate as _process_generate
from contextvars import ContextVar
from copy import deepcopy

_request_capture = ContextVar('request_capture', default=None)


def process_generate(data, *args, **kwargs):
    """保留原脚本行为；构造模式只捕获请求，不上传或提交任务。"""
    capture = _request_capture.get()
    if capture is not None:
        capture.append(deepcopy(data))
        return {}
    return _process_generate(data, *args, **kwargs)


def build_request(kind, config, inputs):
    """将应用节点转换为已有云工作流，ContextVar 避免并发请求互串。"""
    prompt = config.get('prompt', '')
    images = inputs.get('image', [])
    audio = inputs.get('audio', [])
    videos = inputs.get('video', [])
    captured = []
    token = _request_capture.set(captured)
    try:
        if kind in ('image.generate', 'image.variation', 'image.character', 'image.location', 'image.prop'):
            if len(images) > 8:
                raise ValueError('Image2.0 最多支持 8 张参考图')
            if not images:
                generate_gpt_image20_text_2_image(prompt)
            else:
                names = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight']
                globals()['generate_gpt_image20_image2image_' + names[len(images) - 1]](prompt, images)
        elif kind == 'audio.tts':
            if len(audio) > 1:
                raise ValueError('内置声音克隆仅支持 1 段参考音频，请移除多余输入或配置支持多音频的工作流')
            if audio:
                if not config.get('voiceAuthorized'):
                    raise ValueError('使用参考声音前须确认已获得授权')
                generate_audio_clone_voxcpm2(config.get('voiceStyle', ''), prompt, audio[0])
            else:
                generate_audio_qwen_tts(prompt)
        elif kind == 'video.image_to_video':
            if not 1 <= len(images) <= 2:
                raise ValueError('图生视频需要 1 张首帧图或 2 张首尾帧图')
            seconds = float(config.get('seconds', 5))
            if not 1 <= seconds <= 30:
                raise ValueError('视频时长必须在 1–30 秒之间；实际模型限制以云端为准')
            model = config.get('model', 'ltx23')
            if model not in ('ltx23', 'wan22'):
                raise ValueError('不支持的视频模型')
            if model == 'wan22':
                fn = generate_video_single_image_wan22 if len(images) == 1 else generate_video_final_frame_wan22
                fn(prompt, images, seconds=seconds)
            else:
                fn = generate_video_single_image_ltx23 if len(images) == 1 else generate_video_final_frame_ltx23
                fn(prompt, images, seconds=seconds, frame_rate=int(config.get('fps', 25)))
        elif kind == 'video.sound_effects':
            if len(videos) != 1:
                raise ValueError('音效生成需要一个视频输入')
            generate_video_sound_effects_mmaudio(prompt, videos)
        else:
            raise ValueError('未知工作流类型：' + kind)
        return captured[0]
    finally:
        _request_capture.reset(token)

import json

# Image2.0文生图
def generate_gpt_image20_text_2_image(prompt):
    """
    GPT image20 text 2 image
    :param prompt:
    """
    req_data_json = {
        'user_data': [
            {
                "nodeId": "20",
                "fieldName": "text",
                "fieldValue": prompt,
            },
        ],
        'result_node': ['24'],
        'workflowId': '2054172555577184258',
        'nodeInfoList': [
            {
                "nodeId": "35",
                "fieldName": "seed",
                "fieldValue": '123',
            }
        ]

    }
    ret_dict = process_generate(req_data_json)
    if ret_dict.get('result'):
        return ret_dict.get('result')
    else:
        return []


# Image2.0图生图 一张参考图
def generate_gpt_image20_image2image_one(prompt, images):
    """
    参考一张图片
    :param prompt:
    :param image:
    :return:
    """
    req_data_json = {
        'user_data': [
            {
                "nodeId": "9",
                "fieldName": "text",
                "fieldValue": prompt,
            },
            {
                "nodeId": "5",
                "fieldName": "image",
                "fieldValue": images[0],
            },
        ],
        'result_node': ['40'],
        'workflowId': '2055548050453606401',
        'nodeInfoList': [
            {
                "nodeId": "54",
                "fieldName": "seed",
                "fieldValue": '123',
            }
        ]

    }
    ret_dict = process_generate(req_data_json)
    if ret_dict.get('result'):
        return ret_dict.get('result')
    else:
        return []


# Image2.0图生图 两张参考图
def generate_gpt_image20_image2image_two(prompt, images):
    """
    参考2张图片
    :param prompt:
    :param image:
    :return:
    """
    req_data_json = {
        'user_data': [
            {
                "nodeId": "9",
                "fieldName": "text",
                "fieldValue": prompt,
            },
            {
                "nodeId": "5",
                "fieldName": "image",
                "fieldValue": images[0],
            },
            {
                "nodeId": "10",
                "fieldName": "image",
                "fieldValue": images[1],
            },
        ],
        'result_node': ['40'],
        'workflowId': '2055628167523643394',
        'nodeInfoList': [
            {
                "nodeId": "54",
                "fieldName": "seed",
                "fieldValue": '123',
            }
        ]

    }
    ret_dict = process_generate(req_data_json)
    if ret_dict.get('result'):
        return ret_dict.get('result')
    else:
        return []

# Image2.0图生图 3张参考图
def generate_gpt_image20_image2image_three(prompt, images):
    """
    参考3张图片
    :param prompt:
    :param image:
    :return:
    """
    req_data_json = {
        'user_data': [
            {
                "nodeId": "9",
                "fieldName": "text",
                "fieldValue": prompt,
            },
            {
                "nodeId": "5",
                "fieldName": "image",
                "fieldValue": images[0],
            },
            {
                "nodeId": "10",
                "fieldName": "image",
                "fieldValue": images[1],
            },
            {
                "nodeId": "19",
                "fieldName": "image",
                "fieldValue": images[2],
            },
        ],
        'result_node': ['40'],
        'workflowId': '2055832558906159106',
        'nodeInfoList': [
            {
                "nodeId": "54",
                "fieldName": "seed",
                "fieldValue": '123',
            }
        ]

    }
    ret_dict = process_generate(req_data_json)
    if ret_dict.get('result'):
        return ret_dict.get('result')
    else:
        return []


# Image2.0图生图 4张参考图
def generate_gpt_image20_image2image_four(prompt, images):
    """
    参考4张图片
    :param prompt:
    :param image:
    :return:
    """
    req_data_json = {
        'user_data': [
            {
                "nodeId": "9",
                "fieldName": "text",
                "fieldValue": prompt,
            },
            {
                "nodeId": "5",
                "fieldName": "image",
                "fieldValue": images[0],
            },
            {
                "nodeId": "10",
                "fieldName": "image",
                "fieldValue": images[1],
            },
            {
                "nodeId": "19",
                "fieldName": "image",
                "fieldValue": images[2],
            },
            {
                "nodeId": "20",
                "fieldName": "image",
                "fieldValue": images[3],
            },
        ],
        'result_node': ['40'],
        'workflowId': '2055832656901877761',
        'nodeInfoList': [
            {
                "nodeId": "54",
                "fieldName": "seed",
                "fieldValue": '123',
            }
        ]

    }
    ret_dict = process_generate(req_data_json)
    if ret_dict.get('result'):
        return ret_dict.get('result')
    else:
        return []


# Image2.0图生图 5张参考图
def generate_gpt_image20_image2image_five(prompt, images):
    """
    参考5张图片
    :param prompt:
    :param image:
    :return:
    """
    req_data_json = {
        'user_data': [
            {
                "nodeId": "9",
                "fieldName": "text",
                "fieldValue": prompt,
            },
            {
                "nodeId": "5",
                "fieldName": "image",
                "fieldValue": images[0],
            },
            {
                "nodeId": "10",
                "fieldName": "image",
                "fieldValue": images[1],
            },
            {
                "nodeId": "19",
                "fieldName": "image",
                "fieldValue": images[2],
            },
            {
                "nodeId": "20",
                "fieldName": "image",
                "fieldValue": images[3],
            },
            {
                "nodeId": "73",
                "fieldName": "image",
                "fieldValue": images[4],
            },
        ],
        'result_node': ['40'],
        'workflowId': '2055832722865696770',
        'nodeInfoList': [
            {
                "nodeId": "54",
                "fieldName": "seed",
                "fieldValue": '123',
            }
        ]

    }
    ret_dict = process_generate(req_data_json)
    if ret_dict.get('result'):
        return ret_dict.get('result')
    else:
        return []


# Image2.0图生图 6张参考图
def generate_gpt_image20_image2image_six(prompt, images):
    """
    参考6张图片
    :param prompt:
    :param image:
    :return:
    """
    req_data_json = {
        'user_data': [
            {
                "nodeId": "9",
                "fieldName": "text",
                "fieldValue": prompt,
            },
            {
                "nodeId": "5",
                "fieldName": "image",
                "fieldValue": images[0],
            },
            {
                "nodeId": "10",
                "fieldName": "image",
                "fieldValue": images[1],
            },
            {
                "nodeId": "19",
                "fieldName": "image",
                "fieldValue": images[2],
            },
            {
                "nodeId": "20",
                "fieldName": "image",
                "fieldValue": images[3],
            },
            {
                "nodeId": "73",
                "fieldName": "image",
                "fieldValue": images[4],
            },
            {
                "nodeId": "75",
                "fieldName": "image",
                "fieldValue": images[5],
            },
        ],
        'result_node': ['40'],
        'workflowId': '2055840288970690561',
        'nodeInfoList': [
            {
                "nodeId": "54",
                "fieldName": "seed",
                "fieldValue": '123',
            }
        ]

    }
    ret_dict = process_generate(req_data_json)
    if ret_dict.get('result'):
        return ret_dict.get('result')
    else:
        return []


# Image2.0图生图 7张参考图
def generate_gpt_image20_image2image_seven(prompt, images):
    """
    参考7张图片
    :param prompt:
    :param image:
    :return:
    """
    req_data_json = {
        'user_data': [
            {
                "nodeId": "9",
                "fieldName": "text",
                "fieldValue": prompt,
            },
            {
                "nodeId": "5",
                "fieldName": "image",
                "fieldValue": images[0],
            },
            {
                "nodeId": "10",
                "fieldName": "image",
                "fieldValue": images[1],
            },
            {
                "nodeId": "19",
                "fieldName": "image",
                "fieldValue": images[2],
            },
            {
                "nodeId": "20",
                "fieldName": "image",
                "fieldValue": images[3],
            },
            {
                "nodeId": "73",
                "fieldName": "image",
                "fieldValue": images[4],
            },
            {
                "nodeId": "75",
                "fieldName": "image",
                "fieldValue": images[5],
            },
            {
                "nodeId": "77",
                "fieldName": "image",
                "fieldValue": images[6],
            },
        ],
        'result_node': ['40'],
        'workflowId': '2055840689480585218',
        'nodeInfoList': [
            {
                "nodeId": "54",
                "fieldName": "seed",
                "fieldValue": '123',
            }
        ]

    }
    ret_dict = process_generate(req_data_json)
    if ret_dict.get('result'):
        return ret_dict.get('result')
    else:
        return []

# Image2.0图生图 8张参考图
def generate_gpt_image20_image2image_eight(prompt, images):
    """
    参考7张图片
    :param prompt:
    :param image:
    :return:
    """
    req_data_json = {
        'user_data': [
            {
                "nodeId": "9",
                "fieldName": "text",
                "fieldValue": prompt,
            },
            {
                "nodeId": "5",
                "fieldName": "image",
                "fieldValue": images[0],
            },
            {
                "nodeId": "10",
                "fieldName": "image",
                "fieldValue": images[1],
            },
            {
                "nodeId": "19",
                "fieldName": "image",
                "fieldValue": images[2],
            },
            {
                "nodeId": "20",
                "fieldName": "image",
                "fieldValue": images[3],
            },
            {
                "nodeId": "73",
                "fieldName": "image",
                "fieldValue": images[4],
            },
            {
                "nodeId": "75",
                "fieldName": "image",
                "fieldValue": images[5],
            },
            {
                "nodeId": "77",
                "fieldName": "image",
                "fieldValue": images[6],
            },
            {
                "nodeId": "79",
                "fieldName": "image",
                "fieldValue": images[7],
            },
        ],
        'result_node': ['40'],
        'workflowId': '2055841152020033538',
        'nodeInfoList': [
            {
                "nodeId": "54",
                "fieldName": "seed",
                "fieldValue": '123',
            }
        ]

    }
    ret_dict = process_generate(req_data_json)
    if ret_dict.get('result'):
        return ret_dict.get('result')
    else:
        return []


# 声音生成
def generate_audio_qwen_tts(prompt):
    """
    千问声音生成
    prompt示例：
    【角色设定 / Role】\nGender/Age: Female (20s-30s)\nVoice Type: Mezzo-Soprano\nTexture: Smooth, velvety，略带沙哑的性感，如同清晨的薄雾与暖阳交织\nAccent: 吐字清晰，语调中带有一丝异域的慵懒与魅惑，仿佛古老咒语般富有节奏感\n\n【演绎风格 / Style & Emotion】\nEmotion: 神秘、诱惑、自信、平静中蕴含着不容置疑的力量\nTechnique:\n1. Breathy/Vocal Strength: 气声与实声交替，气声用于营造私密与诱惑感，实声则在关键句末展现沉稳的控制力。\n2. Pacing (节奏): 语速缓慢，语句间有意味深长的停顿，如同蛇行般蜿蜒流转，不急不躁。\n3. Intonation (语调): 语调起伏平缓，但每个词语都经过精心雕琢，尾音略微上扬或下沉，带有勾引与试探的意味。\n4. Micro-expressions: 声音中带着一丝不易察觉的微笑，以及对周遭一切尽在掌握的笃定。在特定词汇上，会隐约出现蛇类嘶鸣般的“s”音。

    :param prompt:
    :return:
    """
    req_data_json = {
        'user_data': [
            {
                "nodeId": "31",
                "fieldName": "text",
                "fieldValue": prompt,
            },
        ],
        'result_node': ['15'],
        'workflowId': '2060898589005664258',
        'nodeInfoList': [
            {
                "nodeId": "13",
                "fieldName": "seed",
                "fieldValue": '123',
            }
        ]

    }
    ret_dict = process_generate(req_data_json)
    if ret_dict.get('result'):
        return ret_dict.get('result')
    else:
        return []


# 声音克隆
def generate_audio_clone_voxcpm2(prompt, audio_text, refer_audio):
    """
    voxcpm2声音生成克隆
    prompt示例：
    英语，男性，西部牛仔，沉稳
    audio_text:
    你好，我是小明

    :param prompt: 系统提示词
    :param audio_text: 要说话的文本
    :pram refer_audio: 参考的音频
    :return:
    """
    req_data_json = {
        'user_data': [
            {
                "nodeId": "37",
                "fieldName": "audio",
                "fieldValue": refer_audio,
            },
            {
                "nodeId": "44",
                "fieldName": "text",
                "fieldValue": prompt,
            },
            {
                "nodeId": "39",
                "fieldName": "text",
                "fieldValue": audio_text,
            },
        ],
        'result_node': ['40'],
        'workflowId': '2060540833631395841',
        'nodeInfoList': [
            {
                "nodeId": "34",
                "fieldName": "seed",
                "fieldValue": '123',
            }
        ]

    }
    ret_dict = process_generate(req_data_json)
    if ret_dict.get('result'):
        return ret_dict.get('result')
    else:
        return []


# LTX2.3单图生成视频
def generate_video_single_image_ltx23(prompt_text, images, frame_rate=25, seconds=5, max_length=1920):
    """
    LTX2.3单图生成视频

    :param prompt_text: 提示词
    :param images: 参考的图片数组
    :pram frame_rate: 视频帧率
    :pram seconds: 视频时长，单位秒
    :pram max_length: 视频最大边
    :return:
    """
    req_data_json = {
        'user_data': [
            {
                "nodeId": "115",
                "fieldName": "prompt",
                "fieldValue": prompt_text,
            },
            {
                "nodeId": "111",
                "fieldName": "image",
                "fieldValue": images[0],
            },
            {
                "nodeId": "116",
                "fieldName": "value",
                "fieldValue": frame_rate,
            },
            {
                "nodeId": "112",
                "fieldName": "value",
                "fieldValue": seconds,
            },
            {
                "nodeId": "105",
                "fieldName": "value",
                "fieldValue": max_length,
            },
        ],
        'result_node': ['96'],
        'workflowId': '2060724980819775490',
        'nodeInfoList': [
            {
                "nodeId": "88",
                "fieldName": "noise_seed",
                "fieldValue": '123',
            }
        ]

    }
    ret_dict = process_generate(req_data_json)
    if ret_dict.get('result'):
        return ret_dict.get('result')
    else:
        return []


# LTX2.3首尾帧图生成视频
def generate_video_final_frame_ltx23(prompt_text, images, frame_rate=25, seconds=5, max_length=1920, end_frame=1):
    """
    LTX2.3首尾帧图生成视频

    尾帧的位置说明：
    参数范围：0到1之间，设置为1和-1的效果是一样的，就成为尾帧
    也就是说，首尾帧也可以是首中帧，设置为0.5时，5秒总帧数121帧，一半就是60.5，取余为60，第60帧就是尾帧的意思！
    自由地控制尾帧出现的位置！

    images[0]: 首帧图片   images[1]:尾帧图片

    :param prompt_text: 提示词
    :param images: 参考的图片数组
    :pram frame_rate: 视频帧率
    :pram seconds: 视频时长，单位秒
    :pram max_length: 视频最大边
    :pram end_frame: 尾帧位置
    :return:
    """
    req_data_json = {
        'user_data': [
            {
                "nodeId": "200",
                "fieldName": "prompt",
                "fieldValue": prompt_text,
            },
            {
                "nodeId": "197",
                "fieldName": "image",
                "fieldValue": images[0],
            },
            {
                "nodeId": "198",
                "fieldName": "image",
                "fieldValue": images[1],
            },
            {
                "nodeId": "186",
                "fieldName": "value",
                "fieldValue": frame_rate,
            },
            {
                "nodeId": "199",
                "fieldName": "value",
                "fieldValue": seconds,
            },
            {
                "nodeId": "195",
                "fieldName": "value",
                "fieldValue": end_frame,
            },
            {
                "nodeId": "196",
                "fieldName": "value",
                "fieldValue": max_length,
            },
        ],
        'result_node': ['173'],
        'workflowId': '2060725193840087041',
        'nodeInfoList': [
            {
                "nodeId": "162",
                "fieldName": "noise_seed",
                "fieldValue": '123',
            },
            {
                "nodeId": "156",
                "fieldName": "noise_seed",
                "fieldValue": '123',
            }
        ]

    }
    ret_dict = process_generate(req_data_json)
    if ret_dict.get('result'):
        return ret_dict.get('result')
    else:
        return []


# LTX2.3图生成视频-数字人-强化口型
def generate_video_digital_human_ltx23(prompt_text, images, refer_audio, frame_rate=25, max_length=1920):
    """
    LTX2.3图生成视频-数字人-强化口型
    说话的视频生成适合调用该方法

    :param prompt_text: 提示词
    :param images: 参考的图片数组
    :param refer_audio 参考音频
    :pram frame_rate: 视频帧率
    :pram max_length: 视频最大边
    :return:
    """
    req_data_json = {
        'user_data': [
            {
                "nodeId": "529",
                "fieldName": "text",
                "fieldValue": prompt_text,
            },
            {
                "nodeId": "524",
                "fieldName": "audio",
                "fieldValue": refer_audio,
            },
            {
                "nodeId": "523",
                "fieldName": "image",
                "fieldValue": images[0],
            },
            {
                "nodeId": "530",
                "fieldName": "value",
                "fieldValue": frame_rate,
            },
            {
                "nodeId": "522",
                "fieldName": "value",
                "fieldValue": max_length,
            },
        ],
        'result_node': ['528'],
        'workflowId': '2060725845609771010',
        'nodeInfoList': [
            {
                "nodeId": "512",
                "fieldName": "noise_seed",
                "fieldValue": '123',
            },
            {
                "nodeId": "486",
                "fieldName": "noise_seed",
                "fieldValue": '123',
            }
        ]

    }
    ret_dict = process_generate(req_data_json)
    if ret_dict.get('result'):
        return ret_dict.get('result')
    else:
        return []


# Wan2.2单图生成视频
def generate_video_single_image_wan22(prompt_text, images, seconds=5, max_length=1280):
    """
    Wan2.0单图生成视频

    :param prompt_text: 提示词
    :param images: 参考的图片数组
    :pram seconds: 视频时长，单位秒
    :pram max_length: 视频最大边
    :return:
    """
    req_data_json = {
        'user_data': [
            {
                "nodeId": "36",
                "fieldName": "text",
                "fieldValue": prompt_text,
            },
            {
                "nodeId": "13",
                "fieldName": "image",
                "fieldValue": images[0],
            },
            {
                "nodeId": "15",
                "fieldName": "value",
                "fieldValue": seconds,
            },
            {
                "nodeId": "16",
                "fieldName": "value",
                "fieldValue": max_length,
            },
        ],
        'result_node': ['39'],
        'workflowId': '2065611954248577026',
        'nodeInfoList': [
            {
                "nodeId": "9",
                "fieldName": "noise_seed",
                "fieldValue": '123',
            },
            {
                "nodeId": "25",
                "fieldName": "noise_seed",
                "fieldValue": '123',
            },
        ]

    }
    ret_dict = process_generate(req_data_json)
    if ret_dict.get('result'):
        return ret_dict.get('result')
    else:
        return []


# Wan2.2首尾帧生成视频
def generate_video_final_frame_wan22(prompt_text, images, seconds=5, max_length=1280):
    """
    Wan2.0首尾帧生成视频

    :param prompt_text: 提示词
    :param images: 参考的图片数组
    :pram seconds: 视频时长，单位秒
    :pram max_length: 视频最大边
    :return:
    """
    req_data_json = {
        'user_data': [
            {
                "nodeId": "10",
                "fieldName": "text",
                "fieldValue": prompt_text,
            },
            {
                "nodeId": "48",
                "fieldName": "image",
                "fieldValue": images[0],
            },
            {
                "nodeId": "71",
                "fieldName": "image",
                "fieldValue": images[1],
            },
            {
                "nodeId": "9",
                "fieldName": "value",
                "fieldValue": seconds,
            },
            {
                "nodeId": "8",
                "fieldName": "value",
                "fieldValue": max_length,
            },
        ],
        'result_node': ['51'],
        'workflowId': '2065612669738110977',
        'nodeInfoList': [
            {
                "nodeId": "39",
                "fieldName": "seed",
                "fieldValue": '123',
            }
        ]

    }
    ret_dict = process_generate(req_data_json)
    if ret_dict.get('result'):
        return ret_dict.get('result')
    else:
        return []


# MMAudio视频生成音效
def generate_video_sound_effects_mmaudio(prompt_text, videos):
    """
    MMAudio视频生成音效

    :param prompt_text: 提示词
    :param videos: 参考的视频数组
    :return:
    """
    req_data_json = {
        'user_data': [
            {
                "nodeId": "22",
                "fieldName": "prompt",
                "fieldValue": prompt_text,
            },
            {
                "nodeId": "19",
                "fieldName": "video",
                "fieldValue": videos[0],
            },

        ],
        'result_node': ['24'],
        'workflowId': '2065635022702469121',
        'nodeInfoList': [
            {
                "nodeId": "23",
                "fieldName": "seed",
                "fieldValue": '123',
            }
        ]

    }
    ret_dict = process_generate(req_data_json)
    if ret_dict.get('result'):
        return ret_dict.get('result')
    else:
        return []
