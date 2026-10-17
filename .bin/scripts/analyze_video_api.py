import json
import base64

har_path = r"c:\Users\mkbk\Downloads\www.douyin.com.har"

with open(har_path, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

# 找到作品列表API
for entry in har_data['log']['entries']:
    url = entry['request']['url']
    
    if '/aweme/v1/web/aweme/post/' in url:
        print("="*80)
        print("抖音作品列表API详情")
        print("="*80)
        
        # API地址
        base_url = url.split('?')[0]
        print(f"\n【API基础地址】\n{base_url}\n")
        
        # 必需参数
        print("【核心参数】")
        import urllib.parse
        query = urllib.parse.parse_qs(url.split('?')[1])
        
        essential_params = [
            'device_platform', 'aid', 'channel', 'sec_user_id', 
            'max_cursor', 'count', 'cookie_enabled'
        ]
        
        for param in essential_params:
            if param in query:
                print(f"  {param} = {query[param][0]}")
        
        # 响应数据结构
        response_text = entry['response']['content'].get('text', '')
        if response_text:
            resp_json = json.loads(response_text)
            
            print("\n【响应字段说明】")
            print(f"  status_code: {resp_json.get('status_code')} (0表示成功)")
            print(f"  has_more: {resp_json.get('has_more')} (1表示还有更多)")
            print(f"  max_cursor: {resp_json.get('max_cursor')} (下一页游标)")
            print(f"  aweme_list 数量: {len(resp_json.get('aweme_list', []))}\n")
            
            # 提取第一个视频的完整字段
            if resp_json.get('aweme_list'):
                first_video = resp_json['aweme_list'][0]
                
                print("【单个视频完整字段示例】\n")
                
                # 基础信息
                print("1. 基础信息:")
                print(f"   aweme_id: {first_video.get('aweme_id')}")
                print(f"   desc (文案): {first_video.get('desc')}")
                print(f"   create_time (发布时间戳): {first_video.get('create_time')}")
                
                # 作者信息
                author = first_video.get('author', {})
                print(f"\n2. 作者信息:")
                print(f"   nickname: {author.get('nickname')}")
                print(f"   uid: {author.get('uid')}")
                print(f"   sec_uid: {author.get('sec_uid')}")
                
                # 统计数据
                stats = first_video.get('statistics', {})
                print(f"\n3. 数据统计 (statistics):")
                for key in ['play_count', 'digg_count', 'comment_count', 'share_count', 'collect_count']:
                    print(f"   {key}: {stats.get(key, 'N/A')}")
                
                # 视频信息
                video = first_video.get('video', {})
                print(f"\n4. 视频信息 (video):")
                print(f"   duration: {video.get('duration')} 毫秒")
                print(f"   width: {video.get('width')}")
                print(f"   height: {video.get('height')}")
                
                play_addr = video.get('play_addr', {})
                if play_addr.get('url_list'):
                    print(f"   播放地址: {play_addr['url_list'][0][:80]}...")
                
                # 封面
                cover = video.get('cover', {})
                if cover.get('url_list'):
                    print(f"\n5. 封面图:")
                    print(f"   {cover['url_list'][0][:80]}...")
                
                # 互动信息
                print(f"\n6. 其他字段:")
                print(f"   is_top (是否置顶): {first_video.get('is_top')}")
                print(f"   aweme_type: {first_video.get('aweme_type')}")
                
                # 保存完整结构到文件
                print("\n" + "="*80)
                print("完整单视频JSON结构已保存到 video_structure.json")
                with open('video_structure.json', 'w', encoding='utf-8') as f:
                    json.dump(first_video, f, ensure_ascii=False, indent=2)
        
        break

# 找相关推荐API
print("\n\n" + "="*80)
print("相关推荐API详情")
print("="*80)

for entry in har_data['log']['entries']:
    url = entry['request']['url']
    
    if '/aweme/v1/web/aweme/related/' in url:
        base_url = url.split('?')[0]
        print(f"\n【API基础地址】\n{base_url}\n")
        
        print("【核心参数】")
        query = urllib.parse.parse_qs(url.split('?')[1])
        
        for param in ['aweme_id', 'count', 'filterGids']:
            if param in query:
                print(f"  {param} = {query[param][0]}")
        
        # 解析响应（可能是base64编码）
        response_text = entry['response']['content'].get('text', '')
        if response_text:
            try:
                # 尝试直接解析
                resp_json = json.loads(response_text)
                print("\n【响应格式】JSON")
            except:
                # 可能是base64
                try:
                    decoded = base64.b64decode(response_text).decode('utf-8')
                    resp_json = json.loads(decoded)
                    print("\n【响应格式】Base64编码的JSON")
                except:
                    print("\n【响应格式】未知格式")
                    resp_json = None
            
            if resp_json and 'aweme_list' in resp_json:
                print(f"  返回视频数: {len(resp_json['aweme_list'])}")
                print("  字段结构与作品列表API相同")
        
        break
