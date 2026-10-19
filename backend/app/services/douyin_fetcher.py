"""
抖音数据采集服务（纯 Python）

用 Playwright 打开抖音首页，让页面自己的签名 SDK 生效，
然后在页面上下文里发 XHR，SDK 会自动追加 a_bogus 等参数，
我们只读取返回的 JSON。

对外统一接收视频链接（长链/短链均可），短链通过浏览器跳转后从 location 解析 aweme_id。
"""
import asyncio
import logging
import os
import re
import time
from typing import Callable, Dict, List, Optional
from urllib.parse import urlencode

from playwright.async_api import async_playwright

logger = logging.getLogger('douyin.fetcher')

HOME = 'https://www.douyin.com/'

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36'
)

COMMON_PARAMS = {
    'device_platform': 'webapp',
    'aid': '6383',
    'channel': 'channel_pc_web',
    'pc_client_type': '1',
    'version_code': '170400',
    'version_name': '17.4.0',
    'cookie_enabled': 'true',
    'screen_width': '800',
    'screen_height': '600',
    'browser_language': 'zh-CN',
    'browser_platform': 'Win32',
    'browser_name': 'Chrome',
    'browser_version': '155.0.0.0',
    'browser_online': 'true',
    'engine_name': 'Blink',
    'engine_version': '155.0.0.0',
    'os_name': 'Windows',
    'os_version': '10',
    'cpu_core_num': '4',
    'device_memory': '8',
    'platform': 'PC',
    'downlink': '10',
    'effective_type': '4g',
    'round_trip_time': '50',
}

ID_PATTERNS = [
    re.compile(r'/video/(\d{15,25})'),
    re.compile(r'/note/(\d{15,25})'),
    re.compile(r'/share/video/(\d{15,25})'),
    re.compile(r'/share/note/(\d{15,25})'),
    re.compile(r'[?&]aweme_id=(\d{15,25})'),
]


def extract_aweme_id(url: str) -> Optional[str]:
    """
    从抖音视频长链中快速提取 aweme_id（短链会返回 None，需浏览器跳转后解析）
    """
    if not url:
        return None

    for pattern in ID_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1)

    return None


class DouyinFetcher:
    def __init__(
            self,
            headless: bool = True,
            executable_path: Optional[str] = None,
            concurrency: int = 3,
            retry_times: int = 2,
            retry_delay_seconds: int = 5,
            video_timeout: int = 120,
    ):
        """
        :param headless: 是否无头运行
        :param executable_path: Chrome 可执行文件路径，默认自动探测系统 Chrome
        :param concurrency: 批量采集时的并发页面数
        :param retry_times: 单条请求失败后的重试次数
        :param retry_delay_seconds: 两次重试之间的等待时间
        :param video_timeout: 单条视频采集的硬超时（秒），超时后放弃该条并重建页面
        """
        self.headless = headless
        self.executable_path = executable_path or self._detect_chrome()
        self.concurrency = max(1, concurrency)
        self.retry_times = max(0, retry_times)
        self.retry_delay_seconds = max(1, retry_delay_seconds)
        self.video_timeout = max(30, video_timeout)

    @staticmethod
    def _detect_chrome() -> Optional[str]:
        candidates = [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            '/usr/bin/google-chrome',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None  # 交给 Playwright 使用自带 Chromium

    # ==================== 对外接口 ====================

    def fetch_video_detail(self, url: str) -> Dict:
        """
        获取单个视频详情
        :param url: 视频链接（长链或短链）
        :return: {"url", "aweme_id", "author", "desc", "statistics": {...}} 或 {"url", "error"}
        """
        results = self.fetch_video_details([url], concurrency=1)
        if not results:
            return {'url': url, 'error': 'empty result'}
        return results[0]

    def fetch_video_details(
            self,
            urls: List[str],
            concurrency: Optional[int] = None,
            on_result: Optional[Callable[[int, Dict], None]] = None,
    ) -> List[Dict]:
        """
        批量获取视频详情
        :param urls: 视频链接列表（长链或短链）
        :param concurrency: 并发页面数，默认使用实例配置
        :param on_result: 每完成一条就回调 (index, result)，用于实时写库/打印进度
        :return: [{"url", "aweme_id", "author", "desc", "statistics"}, ...]
        """
        if not urls:
            return []

        return asyncio.run(
            self._fetch_many(urls, concurrency or self.concurrency, on_result)
        )

    # ==================== 内部实现 ====================

    async def _fetch_many(
            self,
            urls: List[str],
            concurrency: int,
            on_result: Optional[Callable[[int, Dict], None]] = None,
    ) -> List[Dict]:
        results: List[Optional[Dict]] = [None] * len(urls)
        concurrency = max(1, min(concurrency, len(urls)))
        logger.info('开始采集：%s 条视频，并发 %s，单条超时 %ss', len(urls), concurrency, self.video_timeout)

        async with async_playwright() as pw:
            started = time.monotonic()
            browser = await asyncio.wait_for(
                pw.chromium.launch(
                    headless=self.headless,
                    executable_path=self.executable_path,
                    args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
                ),
                timeout=60,
            )
            logger.info('浏览器已启动，耗时 %.1fs', time.monotonic() - started)

            context = await asyncio.wait_for(browser.new_context(
                user_agent=USER_AGENT,
                viewport={'width': 800, 'height': 600},
                locale='zh-CN',
            ), timeout=30)

            try:
                pages = []
                for _ in range(concurrency):
                    page = await asyncio.wait_for(context.new_page(), timeout=30)
                    await self._ensure_ready(page)
                    pages.append(page)

                queue: asyncio.Queue = asyncio.Queue()
                for index, url in enumerate(urls):
                    queue.put_nowait((index, url))

                async def worker(page):
                    while True:
                        try:
                            index, url = queue.get_nowait()
                        except asyncio.QueueEmpty:
                            return

                        logger.info('开始采集第 %s 条：%s', index + 1, url)
                        item_started = time.monotonic()
                        try:
                            result = await asyncio.wait_for(
                                self._fetch_one(page, url),
                                timeout=self.video_timeout,
                            )
                        except asyncio.TimeoutError:
                            result = {
                                'url': url,
                                'error': f'单条采集超时（>{self.video_timeout}s）',
                            }
                            page = await self._renew_page(context, page)
                        except Exception as exc:  # noqa: BLE001
                            result = {'url': url, 'error': f'{type(exc).__name__}: {exc}'[:255]}

                        if result.get('reset_page'):
                            page = await self._renew_page(context, page)

                        elapsed = time.monotonic() - item_started
                        if result.get('error'):
                            logger.warning('第 %s 条失败，耗时 %.1fs：%s', index + 1, elapsed, result['error'])
                        else:
                            logger.info('第 %s 条完成，耗时 %.1fs，aweme_id=%s',
                                        index + 1, elapsed, result.get('aweme_id'))

                        results[index] = result
                        if on_result is not None:
                            try:
                                on_result(index, result)
                            except Exception:  # noqa: BLE001
                                logger.exception('进度回写失败 index=%s', index)

                await asyncio.gather(*(worker(page) for page in pages))
            finally:
                try:
                    await asyncio.wait_for(browser.close(), timeout=15)
                except Exception:  # noqa: BLE001
                    logger.warning('关闭浏览器超时，已放弃等待')

        logger.info('本批采集结束：%s 条', len(urls))
        return [item or {'url': urls[i], 'error': 'unknown'} for i, item in enumerate(results)]

    async def _renew_page(self, context, page):
        """页面卡死时销毁并重建，避免后续任务继续复用坏页面。"""
        try:
            await asyncio.wait_for(page.close(), timeout=5)
        except Exception:  # noqa: BLE001
            pass
        try:
            new_page = await asyncio.wait_for(context.new_page(), timeout=15)
            await self._ensure_ready(new_page)
            logger.info('已重建采集页面')
            return new_page
        except Exception:  # noqa: BLE001
            logger.exception('重建采集页面失败')
            return page

    async def _ensure_ready(self, page) -> None:
        """确保页面已加载抖音并完成签名 SDK 初始化"""
        if page.url.startswith(HOME):
            return

        try:
            await page.goto(HOME, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_function(
                '() => !!(window.byted_acrawler && window.byted_acrawler.frontier) || !!window.bdms',
                timeout=20000,
            )
        except Exception:
            # SDK 检测超时也继续尝试，页面自身的 hook 通常已经就绪
            pass

    async def _resolve_aweme_id(self, page, url: str) -> str:
        """把视频链接（含短链）解析成 aweme_id"""
        url = (url or '').strip()

        if re.fullmatch(r'\d{15,25}', url):
            return url

        direct = extract_aweme_id(url)
        if direct:
            return direct

        # 短链：浏览器打开后从 location 拿
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        except Exception:
            # 页面加载慢不影响，跳转通常已经完成
            pass

        await asyncio.sleep(2)

        aweme_id = extract_aweme_id(page.url)
        if aweme_id:
            return aweme_id

        try:
            content = await page.content()
            aweme_id = extract_aweme_id(content)
        except Exception:
            content = ''

        if aweme_id:
            return aweme_id

        raise ValueError(f'无法从链接解析 aweme_id: {page.url}')

    async def _request_json(self, page, url: str) -> Dict:
        """在页面上下文里发 XHR（SDK 自动加签），返回解析后的 JSON"""
        last_error = ''
        attempts = self.retry_times + 1

        for attempt in range(1, attempts + 1):
            res = await page.evaluate(
                """(u) => new Promise((resolve) => {
                    const xhr = new XMLHttpRequest();
                    xhr.open('GET', u, true);
                    xhr.withCredentials = true;
                    xhr.timeout = 20000;
                    xhr.onload = () => resolve({ status: xhr.status, text: xhr.responseText });
                    xhr.onerror = () => resolve({ status: -1, text: '' });
                    xhr.ontimeout = () => resolve({ status: -2, text: '' });
                    xhr.send();
                })""",
                url,
            )

            text = (res or {}).get('text') or ''
            if (res or {}).get('status') == 200 and text.strip().startswith('{'):
                import json
                return json.loads(text)

            last_error = f"status={(res or {}).get('status')}, body={text[:200]}"
            if attempt < attempts:
                await asyncio.sleep(self.retry_delay_seconds)

        raise RuntimeError(f'请求失败: {last_error}')

    async def _fetch_one(self, page, url: str) -> Dict:
        try:
            aweme_id = await asyncio.wait_for(self._resolve_aweme_id(page, url), timeout=45)

            # 短链跳转会把页面带离首页，重新回到首页以恢复 SDK 环境
            await asyncio.wait_for(self._ensure_ready(page), timeout=60)

            params = dict(COMMON_PARAMS)
            params.update({
                'aweme_id': aweme_id,
                'request_source': '600',
                'origin_type': 'quick_player',
            })
            api_url = f'{HOME}aweme/v1/web/aweme/detail/?{urlencode(params)}'

            request_timeout = (self.retry_times + 1) * 25 + self.retry_times * self.retry_delay_seconds
            data = await asyncio.wait_for(self._request_json(page, api_url), timeout=request_timeout)
            if data.get('status_code') != 0:
                return {
                    'url': url,
                    'aweme_id': aweme_id,
                    'error': f"status_code={data.get('status_code')}",
                }

            detail = data.get('aweme_detail') or {}
            statistics = detail.get('statistics') or {}
            author = detail.get('author') or {}

            return {
                'url': url,
                'aweme_id': detail.get('aweme_id') or aweme_id,
                'author': author.get('nickname'),
                'desc': detail.get('desc'),
                'statistics': {
                    'digg_count': statistics.get('digg_count', 0),
                    'comment_count': statistics.get('comment_count', 0),
                    'share_count': statistics.get('share_count', 0),
                    'collect_count': statistics.get('collect_count', 0),
                    'play_count': statistics.get('play_count', 0),
                },
            }
        except asyncio.TimeoutError:
            return {'url': url, 'error': '采集步骤超时', 'reset_page': True}
        except Exception as e:
            return {'url': url, 'error': str(e)}


if __name__ == '__main__':
    fetcher = DouyinFetcher(concurrency=3)
    douyin = fetcher.fetch_video_details(urls=[
        "https://v.douyin.com/iSXuNC-q5eA/"
    ])
    print(douyin)
