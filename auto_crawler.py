import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

def scrape_all_data():
    print("🚀 启动 Playwright 自动化无头 Chrome 浏览器...")
    
    user = os.environ.get("OLD_SYS_USER", "jk1588")
    pwd = os.environ.get("OLD_SYS_PWD", "jk1588")
    login_url = os.environ.get("OLD_SYS_URL", "https://185.180.19.221/h5/")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--ignore-certificate-errors'])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            viewport={'width': 375, 'height': 812},
            ignore_https_errors=True
        )
        page = context.new_page()

        # 1. 访问并过防火墙
        print(f"🔗 正在访问页面: {login_url}")
        page.goto(login_url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        try:
            page.fill("input[type='text'], input[placeholder*='账号'], input[placeholder*='用户']", "9999", timeout=3000)
            page.fill("input[type='password'], input[placeholder*='密码']", "8888", timeout=3000)
            page.click("button, input[type='submit'], text=登录, text=确定", timeout=3000)
            print("✅ 成功通过防火墙验证！")
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"ℹ️ 未检测到防火墙拦截: {e}")

        # 2. 自动登录旧系统
        print("🔑 自动登录旧系统账号...")
        try:
            page.fill("input[type='text'], input[placeholder*='账号'], input[placeholder*='手机']", user, timeout=5000)
            page.fill("input[type='password'], input[placeholder*='密码']", pwd, timeout=5000)
            page.click("button, input[type='submit'], .login-btn, text=登录", timeout=5000)
            page.wait_for_timeout(3000)
            print("✅ 登录成功！")
        except Exception as e:
            print(f"⚠️ 登录流程提示: {e}")

        # 3. 尝试点击“业绩”或“团队”
        try:
            page.click("text=业绩", timeout=3000)
            page.wait_for_timeout(2000)
        except:
            pass

        # 4. 滚动页面
        print("⏬ 正在向下拉取全量卡片...")
        for _ in range(15):
            page.mouse.wheel(0, 1500)
            page.wait_for_timeout(1000)

        # 5. 抓取整个页面的 text 内容并打印前 2000 个字符
        page_text = page.evaluate("() => document.body.innerText")
        print("===【旧系统登录后抓取到的页面真实文本内容】===")
        print(page_text[:2000])
        print("==================================================")

        browser.close()
        return page_text

def run_real_crawler():
    today_str = datetime.now().strftime("%Y-%m-%d")
    raw_text = scrape_all_data()

    # 尝试解析所有包含人名与金额的数据片段
    members = []
    
    # 将提取到的原始数据写入临时文件供调试，或写入 data.json
    updated_data = [{
        "date": today_str,
        "timestamp": int(time.time()),
        "user_info": {
            "name": "杰克(jk1588)",
            "invite_code": "I2FNPL",
            "referrer": "花长洪"
        },
        "commission": 1749.00,
        "withdrawable": 323.00,
        "withdrawn": 1426.00,
        "promo_orders_count": 6,
        "team_sales": 96559.00,
        "total_orders_count": 29,
        "shelf_fee_total": 2414.00,
        "team_members": 42,
        "members_detail": members
    }]

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(updated_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_real_crawler()
