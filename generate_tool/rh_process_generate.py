# -*- coding: utf-8 -*-
# @File:     process_generate.py
# @Author:
# @DateTime: 2025/06/10/17:04
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import os.path
import random
import time
import traceback

import requests
from requests_toolbelt import MultipartEncoder


apiKey = os.environ.get('RUNNINGHUB_API_KEY', '')


def rh_api_upload_file(file_byte):
    url = 'https://www.runninghub.cn/task/openapi/upload'
    headers = {
        'Host': 'www.runninghub.cn',
        'Content-Type': 'application/json',
    }
    params = {
        'apiKey': apiKey,
        'file': ("img.png", file_byte, 'image/png')
    }

    multipart_encoder = MultipartEncoder(fields=params)
    headers['Content-Type'] = multipart_encoder.content_type
    resp = requests.post(url, data=multipart_encoder, headers=headers, timeout=(15, 120))
    if resp.status_code == 200:
        ret_data = resp.json()
        if ret_data.get('code') == 0:
            api_data = ret_data.get('data', {})
            return api_data.get('fileName')
        else:
            print('RunningHub request failed; check provider credentials and quota')
            return None
    else:
        print('RunningHub HTTP error:', resp.status_code)
        return None


def rh_api_generate(data: dict):
    url = 'https://www.runninghub.cn/task/openapi/create'
    headers = {
        'Host': 'www.runninghub.cn',
        'Content-Type': 'application/json',
    }

    body = {
        'apiKey': apiKey,
        'workflowId': '',
        'nodeInfoList': [],
    }
    workflowId = data.get('workflowId')
    nodeInfoList = data.get('nodeInfoList')

    body['workflowId'] = workflowId
    body['nodeInfoList'] = nodeInfoList

    resp = requests.post(url, json=body, headers=headers, timeout=(15, 120))
    if resp.status_code == 200:
        ret_data = resp.json()
        if ret_data.get('code') == 0:
            api_data = ret_data.get('data', {})
            return api_data.get('taskId')
        else:
            print('RunningHub request failed; check provider credentials and quota')
            return None
    else:
        print('RunningHub HTTP error:', resp.status_code)
        return None


def rh_api_select_task(task_id):
    # ["QUEUED","RUNNING","FAILED","SUCCESS"]
    url = 'https://www.runninghub.cn/task/openapi/status'
    headers = {
        'Host': 'www.runninghub.cn',
        'Content-Type': 'application/json',
    }

    body = {
        'apiKey': apiKey,
        'taskId': task_id,
    }
    resp = requests.post(url, json=body, headers=headers, timeout=(15, 120))
    if resp.status_code == 200:
        ret_data = resp.json()
        if ret_data.get('code') == 0:
            api_data = ret_data.get('data', 'FAILED')
            return api_data
        else:
            print('RunningHub request failed; check provider credentials and quota')
            return -1
    else:
        print('RunningHub HTTP error:', resp.status_code)
        return -1


def rh_api_get_output(task_id):
    url = 'https://www.runninghub.cn/task/openapi/outputs'
    headers = {
        'Host': 'www.runninghub.cn',
        'Content-Type': 'application/json',
    }

    body = {
        'apiKey': apiKey,
        'taskId': task_id,
    }
    resp = requests.post(url, json=body, headers=headers, timeout=(15, 120))
    if resp.status_code == 200:
        ret_data = resp.json()
        if ret_data.get('code') == 0:
            api_data = ret_data.get('data', [])
            return api_data
        else:
            print('RunningHub request failed; check provider credentials and quota')
            return None
    else:
        print('RunningHub HTTP error:', resp.status_code)
        return None


def await_result(task_id, wait_time=3, count=0, max_count=900):
    for _ in range(count, max_count + 1):
        task_state = rh_api_select_task(task_id)
        if task_state == 'SUCCESS':
            return rh_api_get_output(task_id)
        if task_state not in ('QUEUED', 'RUNNING'):
            return None
        time.sleep(wait_time)
    return None


def process_nodeInfoList(user_data, nodeInfoList):

    for i in range(len(nodeInfoList)):
        node = nodeInfoList[i]
        if node.get('fieldName') in ['seed', 'noise_seed']:
            nodeInfoList[i]['fieldValue'] = str(random.randint(0, 2147483647))  # 2 **32 -1 = 4294967295
    nodeInfoList.extend(user_data)


def get_url_file_content(url):

    return requests.get(url, timeout=(15, 120)).content


def process_user_data(user_data):

    ret_li = []
    for i in range(len(user_data)):
        node = user_data[i]
        tmp_dict = dict()
        tmp_dict['nodeId'] = node['nodeId']
        tmp_dict['fieldName'] = node['fieldName']
        if node['fieldName'] in ['image', 'video', 'audio']:
            tmp_dict['fieldValue'] = rh_api_upload_file(node['fieldValue'])
        else:
            tmp_dict['fieldValue'] = node['fieldValue']

        ret_li.append(tmp_dict)
    return ret_li


def process_generate(data, wait_time=3, max_count=1200):
    try:
        nodeInfoList = data.get('nodeInfoList', '')
        workflowId = data.get('workflowId')
        user_data = data.get('user_data')
        result_node_list = data.get('result_node', [])

        user_process_data = process_user_data(user_data)
        process_nodeInfoList(user_process_data, nodeInfoList)

        req_data = {
            'workflowId': workflowId,
            'nodeInfoList': nodeInfoList,
        }
        # print(req_data)
        task_id = rh_api_generate(req_data)
        # print(task_id)
        if not task_id:
            return {}
        ret_data_list = await_result(task_id, wait_time, 0, max_count)

        if not ret_data_list:
            return {}

        result_data = list(filter(lambda x: x['nodeId'] in result_node_list, ret_data_list))

        li = []
        for result in result_data:
            result_url = result['fileUrl']
            result_type = result['fileType']
            result_byte = get_url_file_content(result_url)
            li.append({
                'data': result_byte,
                'type': result_type
            })
        return {
            'result': li,
        }

    except:
        print(traceback.format_exc())
        return {}


# ==================== 以下为完整 workflow JSON 提交支持（追加，未改动上方任何原有代码） ====================
import json

# 实测：workflow 模式下 workflowId 仍为必填（空串/缺失返回 code 301 must not be null），
# 但传有效值后接口按文档"忽略 workflowId"执行传入的 workflow，此常量仅作占位
PLACEHOLDER_WORKFLOW_ID = '2054172555577184258'


def rh_api_generate_by_workflow(workflow, workflow_id=None, *, request=None):
    # workflow: 完整工作流（dict 或 JSON 字符串）。指定后接口忽略 workflowId
    # workflow_id: 占位必填值，缺省用 PLACEHOLDER_WORKFLOW_ID
    url = 'https://www.runninghub.cn/task/openapi/create'
    headers = {
        'Host': 'www.runninghub.cn',
        'Content-Type': 'application/json',
    }

    if isinstance(workflow, dict):
        workflow = json.dumps(workflow)
    # 应用可注入自己的鉴权、传输和错误处理，不修改模块全局密钥。
    if request is not None:
        data = request('create', {
            'workflowId': workflow_id or PLACEHOLDER_WORKFLOW_ID,
            'workflow': workflow,
        })
        return data.get('taskId') if isinstance(data, dict) else None

    body = {
        'apiKey': apiKey,
        'workflowId': workflow_id or PLACEHOLDER_WORKFLOW_ID,
        'workflow': workflow,
    }

    resp = requests.post(url, json=body, headers=headers, timeout=(15, 120))
    if resp.status_code == 200:
        ret_data = resp.json()
        if ret_data.get('code') == 0:
            api_data = ret_data.get('data', {})
            return api_data.get('taskId')
        else:
            print('RunningHub request failed; check provider credentials and quota')
            return None
    else:
        print('RunningHub HTTP error:', resp.status_code)
        return None


def process_generate_by_workflow(data, wait_time=3, max_count=1200):
    # data: {'workflow': dict或JSON字符串(API格式), 'user_data': [{nodeId, fieldName, fieldValue}], 'result_node': [nodeId, ...]}
    try:
        workflow = data.get('workflow')
        user_data = data.get('user_data') or []
        result_node_list = data.get('result_node', [])

        if isinstance(workflow, str):
            workflow = json.loads(workflow)
        if not isinstance(workflow, dict):
            print('workflow must be an API-format dict or JSON string')
            return {}

        for node in user_data:
            node_id = str(node['nodeId'])
            field_name = node['fieldName']
            field_value = node['fieldValue']
            if field_name in ['image', 'video', 'audio'] and isinstance(field_value, bytes):
                field_value = rh_api_upload_file(field_value)
                if not field_value:
                    print('upload failed, nodeId: %s' % node_id)
                    return {}
            workflow.setdefault(node_id, {}).setdefault('inputs', {})[field_name] = field_value

        task_id = rh_api_generate_by_workflow(workflow, data.get('workflowId'))
        if not task_id:
            return {}
        ret_data_list = await_result(task_id, wait_time, 0, max_count)

        if not ret_data_list:
            return {}

        result_data = list(filter(lambda x: x['nodeId'] in result_node_list, ret_data_list))

        li = []
        for result in result_data:
            result_url = result['fileUrl']
            result_type = result['fileType']
            result_byte = get_url_file_content(result_url)
            li.append({
                'data': result_byte,
                'type': result_type
            })
        return {
            'result': li,
        }

    except:
        print(traceback.format_exc())
        return {}


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description='RunningHub example: submits a real cloud generation task.')
    parser.add_argument('--image', required=True, type=Path, help='Input reference image')
    parser.add_argument('--output-dir', required=True, type=Path, help='Directory for generated results')
    args = parser.parse_args()
    path = args.image
    with open(path, 'rb') as f:
        file_byte = f.read()
    # api_file_path = rh_api_upload_file(file_byte)
    # print(api_file_path)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    save_path = str(args.output_dir)

    data = {

        'user_data': [
            {
                "name": "图片",
                "nodeId": "20",
                "fieldName": "image",
                "fieldValue": file_byte,
            },
            {
                "name": "文本描述",
                "nodeId": "21",
                "fieldName": "text",
                "fieldValue": "Woman in a green dress walks forward gracefully, slightly swaying her hips. She stops, makes a heart shape with her hands, smiles warmly. Camera slowly zooms out to reveal the cozy room setting.",
            },
            {
                "name": "最大宽度",
                "nodeId": "34",
                "fieldName": "value",
                "fieldValue": '768',
            },
        ],
        'result_node': ['11'],
        'workflowId': '1934890416552484865',
        'nodeInfoList': [
            {
                "nodeId": "13",
                "fieldName": "seed",
                "fieldValue": '12345',
            },

        ]
    }

    # data = {
    #
    #     'user_data': [
    #         {
    #             "name": "图片",
    #             "nodeId": "146",
    #             "fieldName": "image",
    #             "fieldValue": file_byte,
    #         },
    #         {
    #             "name": "文本描述",
    #             "nodeId": "147",
    #             "fieldName": "prompt",
    #             "fieldValue": "Put on a pink dress for the model in the picture, keeping the details of the character unchanged",
    #         },
    #     ],
    #     'result_node': '142',
    #     'workflowId': '1934867523592757250',
    #     'nodeInfoList': [
    #         {
    #             "nodeId": "145",
    #             "fieldName": "seed",
    #             "fieldValue": '12345',
    #         },
    #
    #     ]
    # }

    ret_dict = process_generate(data)

    if ret_dict.get('result'):
        save_file_path = os.path.join(save_path, f"{int(time.time())}.{ret_dict.get('result_type')}")
        with open(save_file_path, 'wb') as f:
            f.write(ret_dict.get('result'))
    else:
        print('error')
    # # ----------------------------------------------------------------------------------------
    # task_id = rh_api_generate(req_data)
    # print('task_id ', task_id)
    #
    # # 1934803206025445378
    # # task_id = 1934812538616086530
    # ret_data = await_result(task_id)
    #
    # print('RunningHub request failed; check provider credentials and quota')
    # """
    # [{'fileUrl': 'https://rh-images.xiaoyaoyou.com/c809c0f87d55210c3cb817cdfa07b5d0/output/pl-vace14b_00018_feoyj_1750131798.mp4', 'fileType': 'mp4', 'taskCostTime': '311', 'nodeId': '11'},
    # {'fileUrl': 'https://rh-images.xiaoyaoyou.com/c809c0f87d55210c3cb817cdfa07b5d0/output/wanvideo_00016_hyzsv_1750131805.mp4', 'fileType': 'mp4', 'taskCostTime': '311', 'nodeId': '2'}]
    # """

    # li = [{'fileUrl': 'https://rh-images.xiaoyaoyou.com/c809c0f87d55210c3cb817cdfa07b5d0/output/pl-vace14b_00018_feoyj_1750131798.mp4', 'fileType': 'mp4', 'taskCostTime': '311', 'nodeId': '11'},
    #     {'fileUrl': 'https://rh-images.xiaoyaoyou.com/c809c0f87d55210c3cb817cdfa07b5d0/output/wanvideo_00016_hyzsv_1750131805.mp4', 'fileType': 'mp4', 'taskCostTime': '311', 'nodeId': '2'}]
    #
    # result_node = '2'
    # result_data = list(filter(lambda x: x['nodeId'] == result_node, li))[0]
    # print(result_data)
