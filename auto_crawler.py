import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

def scrape_all_data():
    print("🚀 启动 Playwright 自动化无头 Chrome 浏览器...")
    
    # 获取 GitHub Secrets 配置的环境变量
    user = os.environ.get("OLD_SYS_USER", "")
    pwd = os.environ.get("OLD_SYS_PWD", "")
    login_url = os.environ.get("OLD_SYS_URL", "http://185.180.19.221") # 请确保环境变量填写了真实旧系统地址
    
    if not user or not pwd:
        raise Exception("❌ 未检测到 OLD_SYS_USER 或 OLD_SYS_PWD 环境变量，请先在 GitHub Secrets 中配置！")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 模拟真实手机/H5浏览器视角
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            viewport={'width': 375, 'height': 812}
        )
        page = context.new_page()

        # ----------------------------------------------------
        # 步骤 1：自动打开旧系统并执行登录
        # ----------------------------------------------------
        print(f"🔗 正在访问旧系统登录页: {login_url}")
        page.goto(login_url, wait_until="networkidle")
        page.wait_for_timeout(2000)

        print("🔑 正在自动填写账号密码并点击登录...")
        # 自动定位输入框（Playwright 会尝试寻找常见的文本框与密码框）
        page.fill("input[type='text'], input[placeholder*='账号'], input[placeholder*='手机']", user)
        page.fill("input[type='password'], input[placeholder*='密码']", pwd)
        page.click("button, input[type='submit'], .login-btn, text=登录")
        page.wait_for_timeout(3000) # 等待登录完成

        # ----------------------------------------------------
        # 步骤 2：跳转/进入到【业绩订单】或【团队统计】页面
        # ----------------------------------------------------
        print("🧭 尝试进入【业绩订单】页面...")
        # 如果页面上有“业绩”或“团队”入口，自动点击
        try:
            page.click("text=业绩", timeout=3000)
        except:
            pass
        page.wait_for_timeout(2000)

        # ----------------------------------------------------
        # 步骤 3：核心逻辑——循环滚动页面，直到所有人员/订单彻底加载完
        # ----------------------------------------------------
        print("⏬ 开始循环向下滚动页面加载全部 29 笔订单和所有团队伙伴...")
        last_height = 0
        scroll_count = 0
        
        while scroll_count < 30: # 设定最大滚动次数
            # 向下滚动 1000 像素
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(1500) # 等待网络异步加载新卡片

            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                # 再次强行触底确认
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)
                if page.evaluate("document.body.scrollHeight") == last_height:
                    print("✅ 页面已触底，所有动态增量数据（卡片/列表）已全部加载完毕！")
                    break
            last_height = new_height
            scroll_count += 1
            print(f"🔄 已进行第 {scroll_count} 次滚动，当前页面总高度: {new_height}px")

        # ----------------------------------------------------
        # 步骤 4：全量解析 DOM 节点数据
        # ----------------------------------------------------
        print("📸 正在提取页面解析到的全部数据...")
        # 提取整个页面的文本内容或特定节点卡片
        extracted_text = page.evaluate("() => document.body.innerText")
        
        browser.close()
        return extracted_text

def run_real_crawler():
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    try:
        raw_content = scrape_all_data()
        print("✅ 自动化抓取流程顺利执行完毕！")
        # 此处拿到真实的 raw_content 后，解析出全部人名与金额格式化写入 json
    except Exception as e:
        print(f"❌ 运行失败，原因: {e}")
        # 如果登录未配置或网址打不开，才会在日志中提示错误信息

if __name__ == "__main__":
    run_real_crawler()
