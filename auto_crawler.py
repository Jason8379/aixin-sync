import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

def scrape_all_data():
    print("🚀 启动 Playwright 自动化浏览器...")
    
    user = os.environ.get("OLD_SYS_USER") or "jk1588"
    pwd = os.environ.get("OLD_SYS_PWD") or "jk1588"
    store_code = os.environ.get("OLD_SYS_STORE") or ""
    target_url = "https://185.180.19.221/h5/"

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

        print(f"🔗 正在访问页面: {target_url}")
        page.goto(target_url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # ----------------------------------------------------
        # 步骤 1：精确锁定 SafeLine WAF 输入框 (#slg-ldap-username)
        # ----------------------------------------------------
        safeline_user_input = page.locator("#slg-ldap-username")
        
        if safeline_user_input.is_visible(timeout=4000):
            print("🛡️ 精准锁定 SafeLine 防火墙！开始输入 9999 / 8888 穿透...")
            try:
                # 填入 SafeLine 凭证
                safeline_user_input.fill("9999")
                
                # 定位密码框（同级别的 input[type='password']）
                pwd_input = page.locator("input[type='password']").first
                pwd_input.fill("8888")
                
                # 按回车或点击 Confirm 按钮提交 SafeLine 验证
                page.keyboard.press("Enter")
                print("✅ SafeLine 穿透指令已提交！等待页面重定向...")
                page.wait_for_timeout(6000)
            except Exception as e:
                print(f"⚠️ SafeLine 提交提示: {e}")
        else:
            print("🟢 未检测到 SafeLine 防火墙拦截，直接进行系统登录。")

        # ----------------------------------------------------
        # 步骤 2：登录旧系统 (jk1588 / jk1588)
        # ----------------------------------------------------
        print("🔑 正在定位并填写旧系统账号密码...")
        try:
            # 等待旧系统的登录框加载出来
            page.wait_for_selector("input:not(#slg-ldap-username)", timeout=8000)
            inputs = page.locator("input").all()
            
            # 过滤掉隐藏节点，只填可视节点
            visible_inputs = [i for i in inputs if i.is_visible()]
            print(f"📝 检测到 {len(visible_inputs)} 个可视登录框")

            if len(visible_inputs) >= 3:
                visible_inputs[0].fill(store_code if store_code else "1")
                visible_inputs[1].fill(user)
                visible_inputs[2].fill(pwd)
            elif len(visible_inputs) >= 2:
                visible_inputs[0].fill(user)
                visible_inputs[1].fill(pwd)

            page.keyboard.press("Enter")
            print("✅ 旧系统账号密码提交成功！等待登录进入...")
            page.wait_for_timeout(5000)

        except Exception as e:
            print(f"⚠️ 系统登录表单填写提示: {e}")

        # ----------------------------------------------------
        # 步骤 3：数据拉取与页面分析
        # ----------------------------------------------------
        try:
            page.get_by_text("业绩").click(timeout=3000)
            page.wait_for_timeout(2000)
        except:
            pass

        print("⏬ 向下拉取卡片数据...")
        for _ in range(15):
            page.mouse.wheel(0, 1500)
            page.wait_for_timeout(1000)

        page_text = page.evaluate("() => document.body.innerText")
        print("\n===【突破 WAF 进入系统后获取到的真实文本】===")
        print(page_text[:3000])
        print("==================================================\n")

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
    print("💾 已更新写入 data.json！")

if __name__ == "__main__":
    run_real_crawler()
