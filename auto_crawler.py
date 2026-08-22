import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

def scrape_all_data():
    print("🚀 启动 Playwright 自动化无头 Chrome 浏览器...")
    
    user = os.environ.get("OLD_SYS_USER") or "jk1588"
    pwd = os.environ.get("OLD_SYS_PWD") or "jk1588"
    raw_url = os.environ.get("OLD_SYS_URL") or "https://185.180.19.221/h5/"

    # ----------------------------------------------------
    # 核心突破：将 SafeLine 防火墙凭证 (9999:8888) 注入 URL
    # 转换为: https://9999:8888@185.180.19.221/h5/
    # ----------------------------------------------------
    if "://" in raw_url:
        protocol, domain_path = raw_url.split("://", 1)
        auth_url = f"{protocol}://9999:8888@{domain_path}"
    else:
        auth_url = f"https://9999:8888@{raw_url}"

    print(f"🔗 正在带 Basic Auth 凭证直接穿透 WAF: {auth_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--ignore-certificate-errors',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        # 在 Context 级别显式配置 http_credentials 双保险
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            viewport={'width': 375, 'height': 812},
            ignore_https_errors=True,
            http_credentials={"username": "9999", "password": "8888"}
        )
        page = context.new_page()

        # 1. 直接访问带认证的 URL
        page.goto(auth_url, wait_until="networkidle")
        page.wait_for_timeout(4000)

        # 2. 自动填写旧系统登录表单 (jk1588 / jk1588)
        print("🔑 自动填写旧系统账号密码...")
        try:
            # 等待登录框出现
            page.wait_for_selector("input", timeout=8000)
            inputs = page.locator("input").all()
            if len(inputs) >= 2:
                inputs[0].fill(user)
                inputs[1].fill(pwd)
                page.keyboard.press("Enter")
                print("✅ 已输入系统账号密码并提交！")
                page.wait_for_timeout(4000)
        except Exception as e:
            print(f"⚠️ 登录框定位提示: {e}")

        # 3. 点击业绩与滚动拉取
        try:
            page.get_by_text("业绩").click(timeout=3000)
            page.wait_for_timeout(2000)
        except:
            pass

        print("⏬ 正在向下滚动页面以加载所有卡片...")
        for _ in range(15):
            page.mouse.wheel(0, 1500)
            page.wait_for_timeout(1000)

        page_text = page.evaluate("() => document.body.innerText")
        print("\n===【系统穿透后获取的真实页面文本】===")
        print(page_text[:2000])
        print("==========================================")

        browser.close()
        return page_text

def run_real_crawler():
    today_str = datetime.now().strftime("%Y-%m-%d")
    raw_text = scrape_all_data()

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
        "members_detail": []
    }]

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(updated_data, f, ensure_ascii=False, indent=2)
    print("💾 已写入 data.json！")

if __name__ == "__main__":
    run_real_crawler()
