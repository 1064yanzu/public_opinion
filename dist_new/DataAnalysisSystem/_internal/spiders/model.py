import csv
import time
import requests


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.42",
    "accept": "application/json, text/plain, */*",
    # 'accept-encoding':'gzip, deflate, br, zstd',
    'accept-language':'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'cookie' : 'ttwid=1%7Ckk--E-9v_tamA3ux-c3AfyOVNO1uGI0juhO9PzETa10%7C1726566141%7C7fb38ba0e7b0148af2ce59df6838ba9580c2fddf37610ee19049939a6d1a7c38; UIFID_TEMP=1ee16134db40129a5ff28e6a352dddaa8524f48fc5e4ea6d697d6a182d7836e4513c0cef87e8fe1b8b50f2161084e3496b48f52a2e7028a9ec9a6051c5a07851b9604854c3420d90a0a91450523474a6a27ad90c1a5e26e2e03c66bf1a5f949c; s_v_web_id=verify_m168wgly_iXKA2eeA_MzEY_4IAf_89qC_C4RDu8XzStw4; hevc_supported=true; dy_swidth=1920; dy_sheight=1080; strategyABtestKey=%221726566142.139%22; passport_csrf_token=499123a680da263bfcd0797ffa9d98ac; passport_csrf_token_default=499123a680da263bfcd0797ffa9d98ac; xgplayer_user_id=282495781594; fpk1=U2FsdGVkX1+xJvzFxrqFursmeVsBihAvo08mhVwYTHb/DdQfe8nIzm90rASbY9q60hraoRnKc9L1YxOico4HXQ==; fpk2=e8db1a910ee088b469ecfd2b6a9b9da5; bd_ticket_guard_client_web_domain=2; SEARCH_RESULT_LIST_TYPE=%22single%22; __ac_nonce=066e95983000586f4c19f; __ac_signature=_02B4Z6wo00f01WrEvHQAAIDB4P5MCqLMCT1q5LjAADxcd75MFFnguBT.vHHmbzkFxVi07OEjk4hv9QmRgENQZd.2gb7Bc5bBt5.zWJFZyjLDTZTRuQi9HMF5ILDtIPjZwrRi5stP3tTUHFLFc5; UIFID=1ee16134db40129a5ff28e6a352dddaa8524f48fc5e4ea6d697d6a182d7836e4513c0cef87e8fe1b8b50f2161084e349a83a3a3048df9c2377cbb77528dd6f8e965cc3bb5d4775ebcce4a3b69bf6968028eae25a854203d21b6fc70141e13ca5a7ddbbbf419009d7c240468a82063ce128dc1831d3e8a0ab88497115a2964d2faebce6ffd4c967f1ca533f1f3d92ddb3e264281519e984d19797be043425b84b9b3c714fdd6ca93d5a93db10c5233059; douyin.com; xg_device_score=7.381583463336465; device_web_cpu_core=8; device_web_memory_size=8; architecture=amd64; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1920%2C%5C%22screen_height%5C%22%3A1080%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A8%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A50%7D%22; csrf_session_id=8ace34d9f0370c0f2dfa964b8d5afa4b; volume_info=%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Atrue%2C%22volume%22%3A0.5%7D; download_guide=%223%2F20240917%2F0%22; WallpaperGuide=%7B%22showTime%22%3A1726568876989%2C%22closeTime%22%3A0%2C%22showCount%22%3A1%2C%22cursor1%22%3A25%2C%22cursor2%22%3A4%7D; pwa2=%220%7C0%7C1%7C0%22; stream_player_status_params=%22%7B%5C%22is_auto_play%5C%22%3A0%2C%5C%22is_full_screen%5C%22%3A0%2C%5C%22is_full_webscreen%5C%22%3A0%2C%5C%22is_mute%5C%22%3A1%2C%5C%22is_speed%5C%22%3A1%2C%5C%22is_visible%5C%22%3A0%7D%22; FORCE_LOGIN=%7B%22videoConsumedRemainSeconds%22%3A180%2C%22isForcePopClose%22%3A1%7D; biz_trace_id=bdeb5adb; passport_mfa_token=CjdNLMU69ySL9fH8j1YrO6dylR%2Fu9cIDk0N%2FykWTe7wc1WYUh9S%2B7Y%2B9%2F7jDNLlxAQXdQn%2FMJ%2BtnGkoKPClb%2Fa1pmo2YreXVH1h4vgiyd8rjdsJhGgzrkBXZiUr06lsioSXbPv%2FAu68F8swygWtgAz39gicXSbmrQRCXrdwNGPax0WwgAiIBA4UAE0A%3D; d_ticket=3f6070eee22bdc09732e0d7422e6bb19b338a; passport_assist_user=CkFTY6yedwHYk656gJO7iNpvWU6j55XyJy1EcNg9Et1-mbe4NoSsutwah95ZJeTxgCkQqqd3PZZpqdhkU3vdFybFEhpKCjwok7DVDBjiSJcDxyaCfDZtVVTKydhjXV2uZurnxlg-pFRTGxQ0nLY-vFPKAnASfzkk_jB1iBr6rqPwfdQQqKzcDRiJr9ZUIAEiAQOQuRQR; n_mh=m6ExldHGHmJ51Zivo9Yurf74nhDftdr_AHxrnX3SSf8; sso_uid_tt=ea68b3bf4355516c3895995880eb319b; sso_uid_tt_ss=ea68b3bf4355516c3895995880eb319b; toutiao_sso_user=18b9e515a484ec2cbf49f9b0b5e52dec; toutiao_sso_user_ss=18b9e515a484ec2cbf49f9b0b5e52dec; sid_ucp_sso_v1=1.0.0-KDBhMmJmZjE4NmMxNGE0NTM2NmYzODhmZGJiMDQwNGVjZGU0ODNjYjcKIQiY_pCGnYzcBhCHvKW3BhjvMSAMMLyxg4EGOAZA9AdIBhoCbGYiIDE4YjllNTE1YTQ4NGVjMmNiZjQ5ZjliMGI1ZTUyZGVj; ssid_ucp_sso_v1=1.0.0-KDBhMmJmZjE4NmMxNGE0NTM2NmYzODhmZGJiMDQwNGVjZGU0ODNjYjcKIQiY_pCGnYzcBhCHvKW3BhjvMSAMMLyxg4EGOAZA9AdIBhoCbGYiIDE4YjllNTE1YTQ4NGVjMmNiZjQ5ZjliMGI1ZTUyZGVj; passport_auth_status=c29a468e2e65b31340ed20c390d54be2%2C; passport_auth_status_ss=c29a468e2e65b31340ed20c390d54be2%2C; uid_tt=4db0aa21e6ad47e150f3da12b76c277b; uid_tt_ss=4db0aa21e6ad47e150f3da12b76c277b; sid_tt=c1b4e20bb3e1c297033c16db920bcca3; sessionid=c1b4e20bb3e1c297033c16db920bcca3; sessionid_ss=c1b4e20bb3e1c297033c16db920bcca3; is_staff_user=false; IsDouyinActive=true; home_can_add_dy_2_desktop=%221%22; SelfTabRedDotControl=%5B%5D; FOLLOW_LIVE_POINT_INFO=%22MS4wLjABAAAAGDd3a3tk9NzqiHpkSg9WzGKMVte88hMfU60AxsSTlZ4YmA1nSfotnBR2cgEmjPou%2F1726588800000%2F0%2F1726569997540%2F0%22; _bd_ticket_crypt_doamin=2; _bd_ticket_crypt_cookie=5eff52d316944afde243b0cbe970666a; __security_server_data_status=1; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCS3RWcFlKa0xnSzNrUVM3TllzMWJoRk1Yd2JVY2dpdTh4RDVFbjEwVlZCVjJxNlJna1ZLbEhqNEdYQWZ5cHhDeVBpYjQ2T0duV1pRMU9GVStpUjdlUG89IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoxfQ%3D%3D; passport_fe_beating_status=true; sid_guard=c1b4e20bb3e1c297033c16db920bcca3%7C1726570000%7C5183994%7CSat%2C+16-Nov-2024+10%3A46%3A34+GMT; sid_ucp_v1=1.0.0-KGJlOTE5YjM4MmQ3NzNkYzEzNmQ0Yzk4N2ExYzQwODU0ZjlhYjE4ZWEKGwiY_pCGnYzcBhCQvKW3BhjvMSAMOAZA9AdIBBoCbGYiIGMxYjRlMjBiYjNlMWMyOTcwMzNjMTZkYjkyMGJjY2Ez; ssid_ucp_v1=1.0.0-KGJlOTE5YjM4MmQ3NzNkYzEzNmQ0Yzk4N2ExYzQwODU0ZjlhYjE4ZWEKGwiY_pCGnYzcBhCQvKW3BhjvMSAMOAZA9AdIBBoCbGYiIGMxYjRlMjBiYjNlMWMyOTcwMzNjMTZkYjkyMGJjY2Ez; publish_badge_show_info=%220%2C0%2C0%2C1726570006706%22; odin_tt=aed80983c6cf6c7b297e62f691821829830643232ca25c4995cc29b4326a5b7fed29bc84dcb87a34fc785b310a24597d',
    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

def spider(url,params):
    response = requests.get(url,params=params,headers=headers)
    response.encoding = 'utf-8'
    return response.json()


def get_douyin_list(v_keyword, v_max_page):
    offset = 0
    count = 16
    url = 'https://sharedchat.fun/GetClaudeAccountList?t=1172502885'




if __name__ == '__main__':
    get_douyin_list('王冰冰',2)


