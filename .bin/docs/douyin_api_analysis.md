# 抖音视频详情获取API分析报告

基于抓包数据 `www.douyin.com.har` 的分析结果

---

## 一、核心API接口

### 1. 作者作品列表API（推荐使用）

**接口地址：**
```
GET https://www.douyin.com/aweme/v1/web/aweme/post/
```

**必需参数：**
| 参数名 | 示例值 | 说明 |
|--------|--------|------|
| device_platform | webapp | 平台标识 |
| aid | 6383 | 应用ID，固定值 |
| channel | channel_pc_web | 渠道标识 |
| sec_user_id | MS4wLjABAAAAEacb... | 作者唯一标识（从作者主页URL提取） |
| count | 18 | 每页返回数量（建议10-20） |
| max_cursor | 0 | 分页游标（首次为0，后续用响应中的max_cursor） |
| cookie_enabled | true | Cookie开关 |

**重要签名参数（必需）：**
- `webid` - 设备标识
- `msToken` - 临时令牌
- `a_bogus` - 防爬签名（最关键）
- `verifyFp` / `fp` - 指纹参数
- `timestamp` - 时间戳
- `x-secsdk-web-signature` - SDK签名

**请求头：**
```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...
Referer: https://www.douyin.com/note/7594469617029339131
Cookie: [需要登录态Cookie]
```

---

### 2. 相关推荐API

**接口地址：**
```
GET https://www.douyin.com/aweme/v1/web/aweme/related/
```

**核心参数：**
| 参数名 | 示例值 | 说明 |
|--------|--------|------|
| aweme_id | 7594469617029339131 | 当前视频ID |
| count | 20 | 推荐数量 |
| filterGids | 7594469617029339131 | 过滤已展示的视频ID |

**响应格式：** Base64编码的JSON（需先解码）

---

## 二、响应数据结构

### 1. 响应外层结构

```json
{
  "status_code": 0,           // 0表示成功
  "min_cursor": 1768225253000,
  "max_cursor": 1748605200000, // 下一页游标
  "has_more": 1,               // 1表示还有更多数据
  "aweme_list": []             // 视频列表
}
```

### 2. 单个视频完整字段（aweme_list中的元素）

#### 基础信息
```json
{
  "aweme_id": "7594469617029339131",
  "desc": "全球十大AI模型...",
  "create_time": 1768225253,  // Unix时间戳（秒）
  "aweme_type": 68,            // 视频类型
  "is_top": 0                  // 是否置顶
}
```

#### 作者信息（author字段）
```json
"author": {
  "uid": "2664837986392663",
  "sec_uid": "MS4wLjABAAAA...",
  "nickname": "A港美风口",
  "avatar_thumb": {
    "url_list": ["https://p3-pc.douyinpic.com/..."]
  },
  "follow_status": 0
}
```

#### 统计数据（statistics字段）⭐ 核心
```json
"statistics": {
  "play_count": 0,          // 播放量（注意：可能为0或隐藏）
  "digg_count": 819,        // 点赞数
  "comment_count": 258,     // 评论数
  "share_count": 85,        // 分享数
  "collect_count": 242,     // 收藏数
  "recommend_count": 7,     // 推荐数
  "admire_count": 0         // 打赏数
}
```

> ⚠️ **重要提示：** 
> - `play_count` 在Web API中经常返回0，这是隐私保护策略
> - 实际播放量可能需要从页面HTML中提取或通过其他端口获取

#### 视频信息（video字段）
```json
"video": {
  "duration": 0,            // 视频时长（毫秒）
  "width": 1536,
  "height": 2704,
  "play_addr": {            // 播放地址
    "url_list": ["https://sf11-cdn-tos.douyinstatic.com/..."]
  },
  "cover": {                // 封面图
    "url_list": ["https://p3-pc-sign.douyinpic.com/..."]
  }
}
```

#### 音乐信息（music字段）
```json
"music": {
  "id": 7594019382658173705,
  "title": "@九州服装创作的原声",
  "author": "九州服装"
}
```

---

## 三、关键技术要点

### 1. 签名参数生成

**a_bogus** 是最关键的反爬参数，生成逻辑：
- 需要分析抖音的混淆JS文件
- 通常涉及：URL参数、User-Agent、时间戳等信息的加密
- 建议方案：
  1. 使用浏览器自动化（Playwright/Selenium）+ 浏览器原生执行
  2. 逆向分析JS后用Python复现（较复杂，容易失效）
  3. 使用第三方签名服务

### 2. Cookie要求

- **必需Cookie字段：**
  - `ttwid` - 设备追踪ID
  - `__ac_nonce` - 随机数
  - `__ac_signature` - 签名
  - `sessionid` - 会话ID（可选，但影响数据完整性）

- **获取方式：**
  1. 浏览器登录后从开发者工具复制
  2. 有效期通常为数小时到数天

### 3. 请求频率控制

- 建议间隔：1-3秒/请求
- 过快会触发验证码或封IP
- 可使用代理池分散请求

---

## 四、完整调用流程

### Python实现示例

```python
import requests
import time
import json

def get_author_videos(sec_user_id, cookie, max_videos=100):
    """
    获取作者全部视频
    
    参数:
        sec_user_id: 作者ID
        cookie: 登录态Cookie字符串
        max_videos: 最多获取数量
    """
    base_url = "https://www.douyin.com/aweme/v1/web/aweme/post/"
    
    all_videos = []
    max_cursor = 0
    
    while len(all_videos) < max_videos:
        # 构建参数
        params = {
            'device_platform': 'webapp',
            'aid': '6383',
            'channel': 'channel_pc_web',
            'sec_user_id': sec_user_id,
            'max_cursor': max_cursor,
            'count': 20,
            'cookie_enabled': 'true',
            # ... 其他参数需要动态生成签名
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 ...',
            'Referer': f'https://www.douyin.com/user/{sec_user_id}',
            'Cookie': cookie
        }
        
        response = requests.get(base_url, params=params, headers=headers)
        data = response.json()
        
        if data['status_code'] != 0:
            print(f"请求失败: {data}")
            break
        
        videos = data.get('aweme_list', [])
        all_videos.extend(videos)
        
        print(f"已获取 {len(all_videos)} 个视频")
        
        # 检查是否还有更多
        if data.get('has_more') != 1:
            break
            
        max_cursor = data.get('max_cursor')
        time.sleep(2)  # 频率控制
    
    return all_videos[:max_videos]

def parse_video_info(video):
    """解析单个视频数据"""
    return {
        'video_id': video['aweme_id'],
        'title': video['desc'],
        'author': video['author']['nickname'],
        'create_time': video['create_time'],
        'like_count': video['statistics']['digg_count'],
        'comment_count': video['statistics']['comment_count'],
        'share_count': video['statistics']['share_count'],
        'collect_count': video['statistics']['collect_count'],
        'play_count': video['statistics']['play_count'],  # 可能为0
        'video_url': f"https://www.douyin.com/video/{video['aweme_id']}",
        'duration': video['video']['duration'],
        'cover_url': video['video']['cover']['url_list'][0] if video['video']['cover']['url_list'] else ''
    }
```

---

## 五、常见问题

### Q1: play_count 为什么总是0？

**原因：** 抖音Web端API对播放量做了隐私保护

**解决方案：**
1. 从HTML页面中提取（服务端渲染时会包含真实数据）
2. 使用移动端API（需要更复杂的签名）
3. 通过浏览器自动化获取渲染后的页面数据

### Q2: a_bogus 签名如何生成？

**方案一：浏览器自动化（推荐）**
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(url)
    # 让浏览器自然执行JS生成签名
```

**方案二：逆向JS**
- 需要定位 `webmssdk.js` 或类似文件
- 分析混淆后的加密逻辑
- 用Python重写（工作量大，容易失效）

### Q3: Cookie多久失效？

- 通常2-7天
- 失效后重新登录获取
- 建议定期更新Cookie池

---

## 六、与现有douyin-author-analyzer Skill的集成

该Skill已提供完整的数据采集脚本，建议使用方式：

```bash
# 1. 配置Cookie
echo "your_cookie_here" > cookie.txt

# 2. 采集数据
python scripts/fetch_author_videos.py \
  --url "https://www.douyin.com/user/MS4wLjABAAAA..." \
  --cookie-file cookie.txt \
  --output videos.json \
  --max 200

# 3. 数据分析
python scripts/process_data.py \
  --input videos.json \
  --output report.csv

# 4. 生成报告
python scripts/generate_report.py \
  --input report.csv \
  --output analysis.md
```

---

## 七、数据字段映射表

| API字段 | 中文名称 | 类型 | 说明 |
|---------|---------|------|------|
| aweme_id | 视频ID | string | 唯一标识 |
| desc | 视频文案 | string | 包含话题标签 |
| create_time | 发布时间 | int | Unix时间戳(秒) |
| statistics.digg_count | 点赞数 | int | |
| statistics.comment_count | 评论数 | int | |
| statistics.share_count | 分享数 | int | |
| statistics.collect_count | 收藏数 | int | |
| statistics.play_count | 播放量 | int | 可能为0 |
| video.duration | 时长 | int | 毫秒 |
| author.nickname | 作者昵称 | string | |
| author.sec_uid | 作者ID | string | 用于获取作品列表 |
| is_top | 置顶标记 | int | 0/1 |

---

## 八、完整JSON示例

完整的单视频数据结构已保存至：
- 文件：`video_structure.json`
- 大小：约50KB
- 包含所有可用字段及嵌套结构

---

**报告生成时间：** 2026-10-18  
**数据来源：** c:\Users\mkbk\Downloads\www.douyin.com.har
