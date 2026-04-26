import httpx
from loguru import logger

async def get_ip_location(ip: str) -> str:
    """
    通过外部接口获取 IP 的地理位置
    使用免费的 ip-api.com (每分钟限 45 次请求)
    """
    if ip in ("127.0.0.1", "localhost", "::1"):
        return "本地回环"
    
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            # lang=zh-CN 返回中文结果
            response = await client.get(f"http://ip-api.com/json/{ip}?lang=zh-CN")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return f"{data.get('regionName', '')} {data.get('city', '')}".strip()
    except Exception as e:
        logger.error(f"[IPLookup] 获取位置失败: {e}")
    
    return "未知"
