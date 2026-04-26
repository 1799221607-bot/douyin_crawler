import time
from loguru import logger

def fetch_douyin_cookie_automated():
    """
    使用 DrissionPage 启动浏览器自动化获取 Cookie。
    1. 弹出浏览器窗口指向抖音
    2. 等待用户登录
    3. 抓取所有 Cookie（包括 HttpOnly）
    4. 返回格式化后的字符串
    """
    try:
        from DrissionPage import ChromiumPage, ChromiumOptions
        co = ChromiumOptions()
        # 可以指定浏览器路径，如果不指定则使用默认安装的 Chrome/Edge
        # co.set_browser_path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe") 
        
        page = ChromiumPage(co)
        logger.info("[CookieFetcher] 正在打开抖音登录页面...")
        page.get("https://www.douyin.com")
        
        # 提示用户
        logger.info("[CookieFetcher] 请在弹出的浏览器窗口中完成登录...")
        
        # 循环检查是否包含关键登录 Cookie (sessionid)
        max_wait = 300 # 5分钟超时
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            cookies = page.cookies()
            cookie_dict = {c['name']: c['value'] for c in cookies}
            
            # 抖音登录成功的标志通常是存在 sessionid_ss 或 sessionid
            if 'sessionid' in cookie_dict or 'sessionid_ss' in cookie_dict:
                logger.info("[CookieFetcher] 检测到登录成功，正在提取 Cookie...")
                
                # 拼接成字符串格式
                cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
                page.quit()
                return cookie_str
            
            time.sleep(2)
            
        page.quit()
        raise Exception("登录超时，未检测到有效 Cookie")
        
    except Exception as e:
        logger.error(f"[CookieFetcher] 自动获取失败: {e}")
        raise e
