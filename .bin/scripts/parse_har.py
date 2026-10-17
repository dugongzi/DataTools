import json
import sys

har_path = r"c:\Users\mkbk\Downloads\www.douyin.com.har"

with open(har_path, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

# 筛选包含视频详情、aweme、note、video等关键字的请求
video_apis = []
for entry in har_data['log']['entries']:
    url = entry['request']['url']
    
    # 筛选条件：包含常见视频相关API路径
    keywords = ['/aweme/', '/note/', '/detail/', '/video/', '/item/', '/post/']
    if any(kw in url.lower() for kw in keywords):
        # 排除静态资源
        if not any(ext in url.lower() for ext in ['.js', '.css', '.png', '.jpg', '.woff', '.gif', '.webp']):
            video_apis.append({
                'url': url,
                'method': entry['request']['method'],
                'status': entry['response']['status'],
                'response_size': len(entry['response']['content'].get('text', ''))
            })

print(f"找到 {len(video_apis)} 个可能的视频API请求\n")

# 按响应大小排序，大的通常包含详情
video_apis.sort(key=lambda x: x['response_size'], reverse=True)

for i, api in enumerate(video_apis[:20], 1):
    print(f"{i}. [{api['method']}] {api['status']}")
    print(f"   Size: {api['response_size']} bytes")
    print(f"   URL: {api['url'][:150]}...")
    print()
