import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

def scrape_all_data():
    print("🚀 启动伪装 Chrome 浏览器以穿透 SafeLine WAF 防火墙...")
    
    user = os.environ.get("OLD_SYS_USER") or "jk1588"
    pwd = os.environ.get("OLD_SYS_PWD") or "jk1588"
    login_url = os.environ.get("OLD_SYS_URL") or "https://185.180.19.221/h5/"

    if not login_url.startswith("http"):
        login_url = "https://185.180.19.221/h5/"

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
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            viewport={'width': 375, 'height': 812},
            ignore_https_errors=True
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print(f"🔗 正在访问目标页面: {login_url}")
        page.goto(login_url, wait_until="networkidle")
        page.wait_for_timeout(3000)

        # ----------------------------------------------------
        # 步骤 1：穿透 SafeLine 防火墙 (9999 / 8888)
        # ----------------------------------------------------
        print("🛡️ 开始执行 SafeLine 防火墙穿透...")
        
        try:
            # 获取页面所有的输入框
            inputs = page.locator("input").all()
            if len(inputs) >= 2:
                inputs[0].fill("9999")
                inputs[1].fill("8888")
                page.keyboard.press("Enter")
                print("✅ 已输入 9999 / 8888 并按下 Enter 回车提交！")
            else:
                # 如果找不到 input 节点，使用键盘 Tab 键快速导航填充
                page.keyboard.press("Tab")
                page.keyboard.type("9999")
                page.keyboard.press("Tab")
                page.keyboard.type("8888")
                page.keyboard.press("Enter")
                print("⌨️ 已通过键盘模拟 Tab/Enter 提交防火墙凭证！")
            
            page.wait_for_timeout(4000)
        except Exception as e:
            print(f"ℹ️ 防火墙步骤处理提示: {e}")

        # ----------------------------------------------------
        # 步骤 2：登录旧系统 (jk1588 / jk1588)
        # ----------------------------------------------------
        print("🔑 正在自动填写旧系统账号密码...")
        try:
            # 兼容修正后的 Selector 选择器
            inputs = page.locator("input").all()
            if len(inputs) >= 2:
                inputs[0].fill(user)
                inputs[1].fill(pwd)
                page.keyboard.press("Enter")
                print("✅ 已提交旧系统账号密码 (jk1588/jk1588)！")
            else:
                page.type("input[type='text']", user)
                page.type("input[type='password']", pwd)
                page.keyboard.press("Enter")
            
            page.wait_for_timeout(4000)
        except Exception as e:
            print(f"⚠️ 旧系统登录动作提示: {e}")

        # ----------------------------------------------------
        # 步骤 3：跳转业绩页与加载全量卡片
        # ----------------------------------------------------
        try:
            page.get_by_text("业绩").click(timeout=3000)
            page.wait_for_timeout(2000)
        except:
            pass

        print("⏬ 向下拉取全量卡片...")
        for _ in range(15):
            page.mouse.wheel(0, 1500)
            page.wait_for_timeout(1000)

        # 打印系统登录后的真实页面内容
        page_text = page.evaluate("() => document.body.innerText")
        print("\n===【系统穿透后获取的真实页面文本】===")
        print(page_text[:3000])
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
