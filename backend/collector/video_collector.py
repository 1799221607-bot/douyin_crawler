import asyncio
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import urlparse, parse_qs

import httpx
import yt_dlp
from loguru import logger

from collector.base import BaseCollector
from utils.abogus import ABogus


class VideoCollector(BaseCollector):
    """
    基于底层 API 和纯 Python A-Bogus 的博主主页视频采集器。
    绕过 yt-dlp 对列表页的解析，彻底解决 JS runtimes 缺失问题。
    单个视频下载时，直接向 yt-dlp 提供免解析的直链进行纯下载。
    """

    collector_type = "video"

    async def collect(self, target: dict, config: dict) -> list[dict]:
        """
        采集博主主页所有视频元数据。
        """
        raw_url = target["user_url"]
        
        # ─── 提取 sec_uid ───
        sec_uid = await self._extract_sec_uid(raw_url)
        if not sec_uid:
            logger.error(f"[VideoCollector] 无法提取 sec_uid: {raw_url}")
            return []

        cookie = config.get("cookie", "")
        self.current_cookie = cookie
        proxy = config.get("proxy")

        logger.info(f"[VideoCollector] 开始通过 API 拉取博主视频: {sec_uid}")
        raw_entries = await self._fetch_user_post_api(sec_uid, cookie, proxy, config)
        
        if not raw_entries:
            return []

        videos = [self._parse_api_entry(entry) for entry in raw_entries]
        logger.info(f"[VideoCollector] 成功获取到 {len(videos)} 条视频元数据")
        return videos

    async def _extract_sec_uid(self, raw_url: str) -> Optional[str]:
        # 正则提取 URL
        url_match = re.search(r'(https?://[^\s]+)', raw_url)
        user_url = url_match.group(1) if url_match else raw_url

        # 短链还原
        if "v.douyin.com" in user_url or "iesdouyin.com" in user_url:
            try:
                async with httpx.AsyncClient(follow_redirects=False) as client:
                    resp = await client.head(user_url, headers={
                        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
                    })
                    if resp.status_code in (301, 302):
                        redirect_url = resp.headers.get("location", "")
                        if redirect_url:
                            user_url = redirect_url
            except Exception as e:
                logger.warning(f"[VideoCollector] 短链还原失败: {e}")

        # 解析 sec_uid
        # 形态 1: /user/MS4wLj...
        match = re.search(r'/user/([A-Za-z0-9_-]+)', user_url)
        if match:
            return match.group(1)
        
        # 形态 2: url 参数中携带 sec_uid=
        if "sec_uid=" in user_url:
            parsed = urlparse(user_url)
            qs = parse_qs(parsed.query)
            if "sec_uid" in qs:
                return qs["sec_uid"][0]

        return None

    async def _fetch_user_post_api(self, sec_uid: str, cookie: str, proxy: Optional[str], config: dict) -> list[dict]:
        base_url = "https://www.douyin.com/aweme/v1/web/aweme/post/"
        
        # 提取或生成 msToken
        import urllib.parse
        import random
        import string
        ms_token = ""
        if cookie:
            match = re.search(r'msToken=([^;]+)', cookie)
            if match:
                ms_token = match.group(1)
        if not ms_token:
            ms_token = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(182)) + "=="
                
        params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "update_version_code": "170400",
            "pc_client_type": "1",
            "version_code": "290100",
            "version_name": "29.1.0",
            "cookie_enabled": "true",
            "screen_width": "1920",
            "screen_height": "1080",
            "browser_language": "zh-CN",
            "browser_platform": "Win32",
            "browser_name": "Chrome",
            "browser_version": "130.0.0.0",
            "browser_online": "true",
            "engine_name": "Blink",
            "engine_version": "130.0.0.0",
            "os_name": "Windows",
            "os_version": "10",
            "cpu_core_num": "12",
            "device_memory": "8",
            "platform": "PC",
            "downlink": "10",
            "effective_type": "4g",
            "round_trip_time": "100",
            "msToken": ms_token,
            "sec_user_id": sec_uid,
            "max_cursor": 0,
            "count": 5 if config.get("fast_mode") else 35,
            "locate_query": "false",
            "show_live_replay_strategy": "1",
            "need_time_list": "1",
            "time_list_query": "0",
            "whale_cut_token": "",
            "cut_version": "1",
            "publish_video_strategy_type": "2"
        }
        
        query_str = urllib.parse.urlencode(params)
        
        # 优先使用账号绑定的 UA，否则使用默认指纹
        user_agent = config.get("user_agent")
        if not user_agent:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        
        from utils.abogus import BrowserFingerprintGenerator
        browser_fp = BrowserFingerprintGenerator.generate_fingerprint("Chrome")
        logger.info(f"[VideoCollector] 使用 User-Agent: {user_agent}")
        
        signer = ABogus(fp=browser_fp, user_agent=user_agent)
        params_with_ab, _ab, ua, _body = signer.generate_abogus(query_str, "")
        logger.info(f"[VideoCollector] A-Bogus 签名完成: a_bogus={_ab[:20]}...")
        
        full_url = f"{base_url}?{params_with_ab}"
        logger.debug(f"[VideoCollector] 最终请求 URL 长度: {len(full_url)}")
        
        headers = {
            "User-Agent": ua,
            "Referer": "https://www.douyin.com/",
            "Cookie": cookie,
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive"
        }
        logger.debug(f"[VideoCollector] 请求头已组装，Cookie 长度: {len(cookie)}")
        
        proxies = {"all://": proxy} if proxy else None
        
        try:
            logger.info("[VideoCollector] 发起最终 httpx 请求...")
            async with httpx.AsyncClient(proxies=proxies, timeout=15.0) as client:
                resp = await client.get(full_url, headers=headers)
                logger.info(f"[VideoCollector] API 请求 HTTP {resp.status_code}")
                
                # 尝试解析 JSON 前先校验状态码
                if resp.status_code != 200:
                    logger.error(f"[VideoCollector] 返回异常内容: {resp.text[:500]}")
                    return []
                    
                try:
                    data = resp.json()
                    logger.info(f"[VideoCollector] JSON 解析成功！包含数据主键: {list(data.keys())[:5]}")
                except Exception as e:
                    logger.error(f"[VideoCollector] JSON 解析失败, 返回文本长度为: {len(resp.text)}, 前 100 字符为: {resp.text[:100]}")
                    return []
                
                aweme_list = data.get("aweme_list", [])
                if not aweme_list and data.get("status_code", 0) != 0:
                    logger.warning(f"[VideoCollector] API 返回非零状态码: {data.get('status_code')}, 数据: {data}")
                return aweme_list
        except Exception as e:
            logger.error(f"[VideoCollector] API 请求失败: {e}")
            return []

    def _parse_api_entry(self, entry: dict) -> dict:
        aweme_id = str(entry.get("aweme_id", ""))
        desc = entry.get("desc", "")
        create_time = entry.get("create_time", 0)
        
        published_at = None
        if create_time:
            # 转换为北京时间 (UTC+8) 的无时区格式
            dt_utc = datetime.fromtimestamp(create_time, timezone.utc)
            dt_bj = dt_utc + timedelta(hours=8)
            published_at = dt_bj.replace(tzinfo=None).isoformat()
        
        video = entry.get("video", {})
        duration = video.get("duration", 0) / 1000.0  # ms 转 s
        
        cover_url = ""
        cover_obj = video.get("cover", {})
        if cover_obj and isinstance(cover_obj, dict):
            url_list = cover_obj.get("url_list", [])
            if url_list:
                cover_url = url_list[0]
                
        play_url = ""
        play_addr = video.get("play_addr", {})
        if play_addr and isinstance(play_addr, dict):
            url_list = play_addr.get("url_list", [])
            if url_list:
                play_url = url_list[0]
                
        statistics = entry.get("statistics", {})
        
        return {
            "aweme_id": aweme_id,
            "title": desc[:200] if desc else "无标题",
            "desc": desc,
            "duration": duration,
            "cover_url": cover_url,
            "play_url": play_url or f"https://www.douyin.com/video/{aweme_id}",
            "like_count": statistics.get("digg_count", 0),
            "comment_count": statistics.get("comment_count", 0),
            "share_count": statistics.get("share_count", 0),
            "collect_count": statistics.get("collect_count", 0),
            "published_at": published_at,
        }

    async def download_video(self, aweme_id: str, play_url: str, creator_name: str, config: dict) -> Optional[str]:
        """
        下载单视频。由于列表解析已拿到播放直链(play_url)，
        这里的 yt-dlp 只作为单纯的文件下载器（它支持断点续传和良好的重试机制），不会触发复杂的 JS 解析。
        """
        download_dir = config.get("download_dir", "./videos")
        cookie = config.get("cookie", "")
        proxy = config.get("proxy")

        save_dir = os.path.join(download_dir, creator_name)
        os.makedirs(save_dir, exist_ok=True)

        ydl_opts = self._build_ydl_opts(cookie=cookie, proxy=proxy)
        ydl_opts["outtmpl"] = os.path.join(save_dir, f"{aweme_id}.%(ext)s")

        # 优先使用直链进行下载，避免触发 yt-dlp 的页面提取逻辑
        target_url = play_url if play_url and play_url.startswith("http") else f"https://www.douyin.com/video/{aweme_id}"

        loop = asyncio.get_event_loop()
        try:
            local_path = await loop.run_in_executor(
                None, lambda: self._do_download(target_url, ydl_opts, save_dir, aweme_id)
            )
            return local_path
        except Exception as e:
            logger.error(f"[VideoCollector] 下载失败 {aweme_id}: {e}")
            return None

    def _build_ydl_opts(self, cookie: str, proxy: Optional[str]) -> dict:
        opts = {
            "quiet": False,
            "verbose": True,
            "no_warnings": False,
            "ignoreerrors": False,
            "nocheckcertificate": True,
        }
        opts["user_agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        
        if proxy:
            opts["proxy"] = proxy
        else:
            opts["proxy"] = ""
            
        opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        opts["merge_output_format"] = "mp4"
            
        if cookie:
            opts["http_headers"] = {
                "Cookie": cookie,
                "Referer": "https://www.douyin.com/"
            }
            
        return opts

    def _do_download(self, url: str, ydl_opts: dict, save_dir: str, aweme_id: str) -> Optional[str]:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        for f in os.listdir(save_dir):
            if aweme_id in f:
                return os.path.join(save_dir, f)
        return None
