import asyncio
import sys
sys.path.append(r"d:\AIWorkSpace3\douyin-downloader-main\douyin-downloader-main")
from core.api_client import DouyinAPIClient
from dotenv import load_dotenv
import os

load_dotenv(r"d:\AIWorkSpace3\douyin_crawler\.env")

async def test_api():
    cookie_str = os.getenv("COOKIE", "")
    print(f"Cookie starts with: {cookie_str[:20] if cookie_str else 'None'}")
    
    # parse cookie string into dict
    cookie_dict = {}
    if cookie_str:
        for item in cookie_str.split(";"):
            if "=" in item:
                k, v = item.strip().split("=", 1)
                cookie_dict[k] = v
                
    client = DouyinAPIClient(cookies=cookie_dict)
    print("Testing get_user_post...")
    res = await client.get_user_post("MS4wLjABAAAA4MbaI7dCSSup9TNRfhmUcDkDzKBhZaogLgvOZ8q-FUrHapV264LIpdzuydoH_gu2")
    print(f"Result raw length: {len(res.get('raw', {}))}")
    print(f"Found {len(res.get('items', []))} items")
    await client.close()

if __name__ == "__main__":
    asyncio.run(test_api())
