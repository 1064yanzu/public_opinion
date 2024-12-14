import csv
import json
import time
import requests
import pandas as pd
import random
from requests.exceptions import RequestException
from typing import Optional, Dict, List
import logging

from utils.common import get_persistent_file_path, get_temp_file_path, update_persistent_file


# 添加日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def get_douyin_list(aweme_id: int = 7428524599048015145, max_page: int = 10) -> List[Dict]:
    cursor = 0
    url = 'https://www.douyin.com/aweme/v1/web/comment/list/'  # 移除末尾问号
    data_list = []
    heads = ['用户名', '粉丝数', 'ip地址', '发布时间', '点赞数', '内容']
    
    # 更新headers，移除重复的User-Agent
    headers = {
        'authority': 'www.douyin.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'cookie': 'UIFID_TEMP=1ee16134db40129a5ff28e6a352dddaa8524f48fc5e4ea6d697d6a182d7836e4513c0cef87e8fe1b8b50f2161084e3496b48f52a2e7028a9ec9a6051c5a07851b9604854c3420d90a0a91450523474a6a27ad90c1a5e26e2e03c66bf1a5f949c; s_v_web_id=verify_m168wgly_iXKA2eeA_MzEY_4IAf_89qC_C4RDu8XzStw4; hevc_supported=true; passport_csrf_token=499123a680da263bfcd0797ffa9d98ac; passport_csrf_token_default=499123a680da263bfcd0797ffa9d98ac; xgplayer_user_id=282495781594; fpk1=U2FsdGVkX1+xJvzFxrqFursmeVsBihAvo08mhVwYTHb/DdQfe8nIzm90rASbY9q60hraoRnKc9L1YxOico4HXQ==; fpk2=e8db1a910ee088b469ecfd2b6a9b9da5; bd_ticket_guard_client_web_domain=2; SEARCH_RESULT_LIST_TYPE=%22single%22; UIFID=1ee16134db40129a5ff28e6a352dddaa8524f48fc5e4ea6d697d6a182d7836e4513c0cef87e8fe1b8b50f2161084e349a83a3a3048df9c2377cbb77528dd6f8e965cc3bb5d4775ebcce4a3b69bf6968028eae25a854203d21b6fc70141e13ca5a7ddbbbf419009d7c240468a82063ce128dc1831d3e8a0ab88497115a2964d2faebce6ffd4c967f1ca533f1f3d92ddb3e264281519e984d19797be043425b84b9b3c714fdd6ca93d5a93db10c5233059; volume_info=%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Atrue%2C%22volume%22%3A0.5%7D; passport_mfa_token=CjdNLMU69ySL9fH8j1YrO6dylR%2Fu9cIDk0N%2FykWTe7wc1WYUh9S%2B7Y%2B9%2F7jDNLlxAQXdQn%2FMJ%2BtnGkoKPClb%2Fa1pmo2YreXVH1h4vgiyd8rjdsJhGgzrkBXZiUr06lsioSXbPv%2FAu68F8swygWtgAz39gicXSbmrQRCXrdwNGPax0WwgAiIBA4UAE0A%3D; d_ticket=3f6070eee22bdc09732e0d7422e6bb19b338a; SelfTabRedDotControl=%5B%5D; _bd_ticket_crypt_doamin=2; __security_server_data_status=1; store-region-src=uid; ttwid=1%7Ckk--E-9v_tamA3ux-c3AfyOVNO1uGI0juhO9PzETa10%7C1729524170%7C11749b781c49d89681a00aaa734988a16b363f2c943aa997a379d8002781f8e6; __ac_signature=_02B4Z6wo00f01tjbo5QAAIDD9lxuvowG4e7Y-6cAANE63hoMj4hZ-T8dgURc60FdWryXydzNLfPwnG0jQrdRIXMiBY-oxjGF8pdgqeS9q2wzj-aLwgbvAfE3jzVz.g6fWZXZNbAPh4XStMJD62; douyin.com; device_web_cpu_core=8; device_web_memory_size=8; architecture=amd64; dy_swidth=1366; dy_sheight=768; csrf_session_id=fcfa20e90710c1e46193e0df0b467740; strategyABtestKey=%221729844612.854%22; FORCE_LOGIN=%7B%22videoConsumedRemainSeconds%22%3A180%7D; xg_device_score=7.658235294117647; passport_assist_user=CkFpCP8X9M4htO1lZI7Yfa5ozr4pxcoXywgzZyM9vQNT8xA2hOacV0tpAdj0U8kENiDaHrd4ZtfyjYBxaMTOeKM0CxpKCjwrwRO_G_b5eaXYOFSPuydZWkdNmcsoNpJxwXz0Wz9cMwsy3fk7q-Z41GKfnzTLMpjTQGdBMORuVbB7AGwQztXfDRiJr9ZUIAEiAQOmxbFL; n_mh=mtxI9IR7an20kFsHYOuEgKw0tNeo7KR-JyiZaOD2sVE; sso_uid_tt=c109c158ddd08d306ddce2f059a0c258; sso_uid_tt_ss=c109c158ddd08d306ddce2f059a0c258; toutiao_sso_user=32d9f15cfe92d381ba1879c6da7ee289; toutiao_sso_user_ss=32d9f15cfe92d381ba1879c6da7ee289; sid_ucp_sso_v1=1.0.0-KDE5ZWY3MTEwNWY4ZDJjNWMwNjY5YzczOTY5NmFlYWI2NTk3ZDk4NTQKIQjz7uDo0c2sBRDjq-24BhjvMSAMMIakx6YGOAZA9AdIBhoCaGwiIDMyZDlmMTVjZmU5MmQzODFiYTE4NzljNmRhN2VlMjg5; ssid_ucp_sso_v1=1.0.0-KDE5ZWY3MTEwNWY4ZDJjNWMwNjY5YzczOTY5NmFlYWI2NTk3ZDk4NTQKIQjz7uDo0c2sBRDjq-24BhjvMSAMMIakx6YGOAZA9AdIBhoCaGwiIDMyZDlmMTVjZmU5MmQzODFiYTE4NzljNmRhN2VlMjg5; passport_auth_status=fa06899f5c3f3d21be8965a5dc1cde17%2C; passport_auth_status_ss=fa06899f5c3f3d21be8965a5dc1cde17%2C; uid_tt=8544b55bf4d7f78f110050671f5db7f3; uid_tt_ss=8544b55bf4d7f78f110050671f5db7f3; sid_tt=68906a88cff42f5f576f2218c0842836; sessionid=68906a88cff42f5f576f2218c0842836; sessionid_ss=68906a88cff42f5f576f2218c0842836; is_staff_user=false; _bd_ticket_crypt_cookie=2c6f8fe989baf963c04faabbf51b9c58; publish_badge_show_info=%220%2C0%2C0%2C1729844718264%22; sid_guard=68906a88cff42f5f576f2218c0842836%7C1729844718%7C5183992%7CTue%2C+24-Dec-2024+08%3A25%3A10+GMT; sid_ucp_v1=1.0.0-KDFiNDY4MmE5ZTFhMDc4NjY5ODc1NWJiNGM3ZWI2M2E1YmFiYmJhNTkKGwjz7uDo0c2sBRDuq-24BhjvMSAMOAZA9AdIBBoCbGYiIDY4OTA2YTg4Y2ZmNDJmNWY1NzZmMjIxOGMwODQyODM2; ssid_ucp_v1=1.0.0-KDFiNDY4MmE5ZTFhMDc4NjY5ODc1NWJiNGM3ZWI2M2E1YmFiYmJhNTkKGwjz7uDo0c2sBRDuq-24BhjvMSAMOAZA9AdIBBoCbGYiIDY4OTA2YTg4Y2ZmNDJmNWY1NzZmMjIxOGMwODQyODM2; biz_trace_id=c45de2a4; store-region=cn-sd; stream_player_status_params=%22%7B%5C%22is_auto_play%5C%22%3A0%2C%5C%22is_full_screen%5C%22%3A0%2C%5C%22is_full_webscreen%5C%22%3A0%2C%5C%22is_mute%5C%22%3A1%2C%5C%22is_speed%5C%22%3A1%2C%5C%22is_visible%5C%22%3A0%7D%22; FOLLOW_LIVE_POINT_INFO=%22MS4wLjABAAAAmrZC-Gp_6-z1L949tY7lj7YPln_shtHTTgGW-RW7K7Egu9cNSdWPOzzxXOHazEN1%2F1729872000000%2F0%2F0%2F1729845392442%22; FOLLOW_NUMBER_YELLOW_POINT_INFO=%22MS4wLjABAAAAmrZC-Gp_6-z1L949tY7lj7YPln_shtHTTgGW-RW7K7Egu9cNSdWPOzzxXOHazEN1%2F1729872000000%2F0%2F1729844792450%2F0%22; download_guide=%223%2F20241025%2F0%22; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1366%2C%5C%22screen_height%5C%22%3A768%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A8%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A150%7D%22; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCS3RWcFlKa0xnSzNrUVM3TllzMWJoRk1Yd2JVY2dpdTh4RDVFbjEwVlZCVjJxNlJna1ZLbEhqNEdYQWZ5cHhDeVBpYjQ2T0duV1pRMU9GVStpUjdlUG89IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoyfQ%3D%3D; home_can_add_dy_2_desktop=%221%22; odin_tt=3518cb8667948e277a464687818e15bb1ca68f1c274630f54875f76804369971e1c2c544f2ea9c464c4aacf335b3beef; pwa2=%220%7C0%7C2%7C0%22; passport_fe_beating_status=true; IsDouyinActive=true',  # 建议更新cookie
        'referer': f'https://www.douyin.com/video/{aweme_id}',  # 修改referer格式
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        for i in range(max_page):
            # 更新请求参数
            params = {
                'device_platform': 'webapp',
                'aid': '6383',
                'channel': 'channel_pc_web',
                'aweme_id': str(aweme_id),
                'cursor': str(cursor),
                'count': '20',
                'item_type': '0',
                'pc_client_type': '1',
                'version_code': '170400',
                'version_name': '17.4.0'
            }

            try:
                r_data = requests.get(url, params=params, headers=headers, timeout=10)
                print(r_data)
                r_data.raise_for_status()  # 检查响应状态
                json_data = r_data.json()

                try:
                    json_data = r_data.json()
                    print(json.dumps(json_data, indent=2, ensure_ascii=False))
                except json.JSONDecodeError:
                    print("响应内容不是有效的JSON格式:")
                    print(r_data.text)
                
                # 添加响应调试信息
                logging.info(f"Response status: {r_data.status_code}")
                logging.info(f"Response headers: {r_data.headers}")
                logging.debug(f"Response content: {r_data.text[:200]}...")  # 只打印前200个字符
                
                if 'comments' not in json_data:
                    logging.error(f"未找到评论数据: {json_data.get('message', '未知错误')}")
                    continue

                if 'data' not in json_data:
                    logging.warning(f"页面 {i + 1} 没有数据")
                    break

                for data in json_data['data']:
                    try:
                        analyzed_data = analysis_data(data)
                        if analyzed_data:
                            data_list.append(analyzed_data)
                    except Exception as e:
                        logging.error(f"数据解析错误: {str(e)}")
                        continue

                if json_data.get('has_more') == 0:
                    logging.info("已到达最后一页")
                    break

                cursor += 20
                logging.info(f'成功爬取第 {i + 1} 页数据')
                # 添加随机延迟
                time.sleep(random.uniform(2, 5))

            except requests.exceptions.RequestException as e:
                logging.error(f"请求失败: {str(e)}")
                time.sleep(random.uniform(5, 10))  # 失败后增加延迟
                continue

        # 数据保存部分
        if data_list:
            df = pd.DataFrame(data_list, columns=heads)
            
            try:
                persistent_file = get_persistent_file_path('douyin', aweme_id)
                temp_file = get_temp_file_path('douyin')
                
                df.to_csv(temp_file, index=False, encoding='utf-8-sig')
                update_persistent_file(persistent_file, temp_file)
                logging.info(f"数据已保存到文件: {persistent_file}")
            except Exception as e:
                logging.error(f"保存文件失败: {str(e)}")

        return data_list

    except Exception as e:
        logging.error(f"爬虫运行出错: {str(e)}")
        return []

def trans_time(timestamp=None):
    # 如果没有传入时间戳，则使用当前时间
    if timestamp is None:
        timeArray = time.localtime()
    else:
        # 将传入的时间戳转换为时间元组
        timeArray = time.localtime(timestamp)

    # 格式化时间
    real_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)

    # 返回格式化后的时间
    return real_time

def analysis_data(v_data: Dict) -> Optional[Dict]:
    try:
        comments = v_data.get('comments', {})
        if not comments:
            return None

        return {
            '用户名': comments.get('user', {}).get('nickname', '未知用户'),
            '粉丝数': comments.get('user', {}).get('uid', '0'),
            'ip地址': comments.get('ip_label', '未知'),
            '发布时间': trans_time(comments.get('create_time')),
            '点赞数': comments.get('digg_count', 0),
            '内容': comments.get('text', ''),
        }
    except Exception as e:
        logging.error(f"数据解析错误: {str(e)}")
        return None

if __name__ == '__main__':
    get_douyin_list(aweme_id = 7428524599048015145, max_page = 2)

