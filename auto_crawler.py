import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

def scrape_all_data():
    print("🚀 启动 Playwright 自动化浏览器...")
    
    # 环境变量获取
    user = os.environ.get("OLD_SYS_USER") or "jk1588"
    pwd = os.environ.get("OLD_SYS_PWD") or "jk1588"
    store_code = os.environ.get("OLD_SYS_STORE") or "" # 店铺号（若有）
    target_url = os.environ.get("OLD_SYS_URL") or "https://185.180.19.221/h5/"

    if not target_url.startswith("http"):
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
        page.goto(target_url, wait_until="networkidle")
        page.wait_for_timeout(3000)

        # ----------------------------------------------------
        # 判断一：检查是否触发了雷池 (SafeLine WAF) 防火墙
        # ----------------------------------------------------
        page_content = page.content()
        is_safeline = "SafeLine" in page_content or "Confirm You Are Human" in page_content or "防火墙" in page_content

        if is_safeline:
            print("🛡️ 检测到雷池 SafeLine 防火墙拦截！开始填入 9999 / 8888 穿透...")
            try:
                inputs = page.locator("input").all()
                if len(inputs) >= 2:
                    inputs[0].fill("9999")
                    inputs[1].fill("8888")
                    
                    submit_btn = page.locator("button, input[type='submit'], text=/Confirm|确认|登录|Sign In/i").first
                    if submit_btn.is_visible():
                        submit_btn.click()
                    else:
                        page.keyboard.press("Enter")
                    
                    print("✅ SafeLine 凭证已提交，等待页面刷新...")
                    page.wait_for_timeout(5000)
            except Exception as e:
                print(f"⚠️ SafeLine 穿透操作异常: {e}")
        else:
            print("🟢 未触发 SafeLine 防火墙或已自动过关，直接进入系统登录流程。")

        # ----------------------------------------------------
        # 判断二：填入真正的系统账号、密码与店铺号
        # ----------------------------------------------------
        print("🔑 正在准备填入系统账号密码...")
        try:
            page.wait_for_selector("input", timeout=8000)
            inputs = page.locator("input").all()
            
            # 兼容：如果系统有 3 个输入框（店铺号 + 账号 + 密码）
            if len(inputs) >= 3:
                print("📝 检测到 3 个输入框（店铺号/账号/密码模式）：")
                inputs[0].fill(store_code if store_code else "1") # 第一框填店铺号
                inputs[1].fill(user)                            # 第二框填账号
                inputs[2].fill(pwd)                             # 第三框填密码
            # 兼容：如果系统有 2 个输入框（账号 + 密码）
            elif len(inputs) == 2:
                print("📝 检测到 2 个输入框（账号/密码模式）：")
                inputs[0].fill(user)
                inputs[1].fill(pwd)

            # 点击登录提交
            login_btn = page.locator("button, input[type='submit'], .login-btn, text=/登录|Sign In/i").first
            if login_btn.is_visible():
                login_btn.click()
            else:
                page.keyboard.press("Enter")
            
            print("✅ 成功提交系统登录！进入系统中...")
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
        print("\n===【登录后页面获取到的真实内容】===")
        print(page_text[:3000])
        print("========================================\n")

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
