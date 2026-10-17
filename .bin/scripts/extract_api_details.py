import json
import re

har_path = r"c:\Users\mkbk\Downloads\www.douyin.com.har"

with open(har_path, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

# 提取最关键的几个API
target_apis = []
for entry in har_data['log']['entries']:
    url = entry['request']['url']
    
    # 关注这几个API
    if '/note/' in url and 'douyin.com/note/' in url:
        target_apis.append(('note_detail_page', entry))
    elif '/aweme/v1/web/aweme/related/' in url:
        target_apis.append(('related_videos', entry))
    elif '/aweme/v1/web/aweme/post/' in url:
        target_apis.append(('author_posts', entry))

print(f"找到 {len(target_apis)} 个核心API\n")

for api_name, entry in target_apis[:5]:
    print(f"{'='*80}")
    print(f"API类型: {api_name}")
    print(f"{'='*80}\n")
    
    # 请求信息
    print("【请求信息】")
    print(f"URL: {entry['request']['url']}")
    print(f"Method: {entry['request']['method']}")
    print(f"Status: {entry['response']['status']}\n")
    
    # 请求头
    print("【关键请求头】")
    headers = {h['name']: h['value'] for h in entry['request']['headers']}
    important_headers = ['cookie', 'referer', 'user-agent']
    for h in important_headers:
        if h in headers:
            val = headers[h]
            if len(val) > 100:
                val = val[:100] + '...'
            print(f"  {h}: {val}")
    print()
    
    # Query参数
    if '?' in entry['request']['url']:
        print("【URL参数】")
        query_str = entry['request']['url'].split('?')[1].split('#')[0]
        params = query_str.split('&')
        for p in params[:15]:  # 只看前15个
            print(f"  {p}")
        if len(params) > 15:
            print(f"  ... 还有 {len(params) - 15} 个参数")
        print()
    
    # 响应内容（截取）
    response_text = entry['response']['content'].get('text', '')
    if response_text:
        try:
            resp_json = json.loads(response_text)
            print("【响应结构】")
            print(json.dumps(resp_json, ensure_ascii=False, indent=2)[:2000])
            print("\n... (内容已截断)")
        except:
            print(f"【响应内容（前500字符）】")
            print(response_text[:500])
    
    print("\n\n")
