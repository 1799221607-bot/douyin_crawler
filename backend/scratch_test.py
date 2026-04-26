import asyncio
import httpx
import re
import urllib.parse
import json

async def test_html():
    url = "https://www.douyin.com/user/MS4wLjABAAAA4MbaI7dCSSup9TNRfhmUcDkDzKBhZaogLgvOZ8q-FUrHapV264LIpdzuydoH_gu2"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.douyin.com/"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, headers=headers)
        print("Status:", resp.status_code)
        
        # 查找 RENDER_DATA
        match = re.search(r'<script id="RENDER_DATA" type="application/json">([^<]+)</script>', resp.text)
        if match:
            raw_data = match.group(1)
            try:
                decoded = urllib.parse.unquote(raw_data)
                data = json.loads(decoded)
                print("Successfully extracted RENDER_DATA JSON.")
                
                # 寻找视频列表
                for key, val in data.items():
                    if isinstance(val, dict) and "post" in val:
                        post_data = val["post"]
                        if "data" in post_data:
                            print(f"Found {len(post_data['data'])} videos!")
                            for item in post_data["data"][:2]:
                                print("-", item.get("desc", ""))
                            return
                
                # 其他可能的路径
                app = data.get("app", {})
                user_detail = app.get("user_detail", {})
                post_data = user_detail.get("post", {})
                videos = post_data.get("data", [])
                if videos:
                    print(f"Found {len(videos)} videos in app.user_detail.post!")
                    for item in videos[:2]:
                        print("-", item.get("desc", ""))
                    return
            except Exception as e:
                print("Failed to decode or parse:", e)
        else:
            print("RENDER_DATA not found in HTML!")

if __name__ == "__main__":
    asyncio.run(test_html())
