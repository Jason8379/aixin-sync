import os
import json
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

def run_crawler():
    print("🚀 启动爬虫...")
    
    FIREWALL_USER = "9999"
    FIREWALL_PWD = "8888"
    SYS_USER = "jk1588"
    SYS_PWD = "jk1588"
    STORE_NAME = "XYGDP222222"
    TARGET_URL = "https://185.180.19.221/h5/"
    DATA_FILE = "data.json"
    
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
        
        print(f"🌐 访问: {TARGET_URL}")
        page.goto(TARGET_URL, wait_until="networkidle")
        page.wait_for_timeout(4000)
        
        # ---------- 第一步：防火墙认证 ----------
        print("🛡️ 处理防火墙...")
        try:
            page.wait_for_selector("input", timeout=8000)
            inputs = page.locator("input").all()
            visible_inputs = [i for i in inputs if i.is_visible()]
            if len(visible_inputs) >= 2:
                visible_inputs[0].fill(FIREWALL_USER)
                visible_inputs[1].fill(FIREWALL_PWD)
                page.keyboard.press("Enter")
                print("✅ 防火墙凭证已提交")
                page.wait_for_timeout(5000)
        except Exception as e:
            print(f"⚠️ 防火墙跳过: {e}")
        
        # ---------- 第二步：系统登录 ----------
        print("🔑 登录系统...")
        try:
            page.wait_for_selector("input", timeout=10000)
            inputs = page.locator("input").all()
            visible_inputs = [i for i in inputs if i.is_visible()]
            
            if len(visible_inputs) >= 3:
                visible_inputs[0].fill(STORE_NAME)
                visible_inputs[1].fill(SYS_USER)
                visible_inputs[2].fill(SYS_PWD)
            elif len(visible_inputs) >= 2:
                visible_inputs[0].fill(SYS_USER)
                visible_inputs[1].fill(SYS_PWD)
            
            login_btn = page.locator("button:has-text('立即登录')")
            if login_btn.count() > 0:
                login_btn.click()
            else:
                page.keyboard.press("Enter")
            
            print("✅ 登录信息已提交")
            page.wait_for_timeout(5000)
        except Exception as e:
            print(f"❌ 登录失败: {e}")
            browser.close()
            return
        
        # ---------- 第三步：进入“记账中心”（按位置点击底部第三个图标） ----------
        print("📊 进入记账中心（点击底部导航第三项）...")
        try:
            # 方法1：尝试用 aria-label 或 class 定位底部导航
            nav_selectors = [
                ".tabbar-item",
                ".van-tabbar-item",
                ".bottom-nav a",
                ".footer-menu li",
                "[role='tab']",
                ".nav-item"
            ]
            
            clicked = False
            for selector in nav_selectors:
                items = page.locator(selector).all()
                if len(items) >= 3:
                    items[2].click()
                    print(f"   ✅ 已点击第三项 (selector: {selector})")
                    clicked = True
                    break
            
            # 方法2：如果上面没找到，尝试用 xpath 定位第三个可点击元素
            if not clicked:
                third_tab = page.locator("xpath=(//div[@class='tabbar-item' or contains(@class, 'tab')])[3]")
                if third_tab.count() > 0:
                    third_tab.click()
                    clicked = True
                    print("   ✅ 已点击第三个 tab")
            
            # 方法3：如果还是没找到，打印页面全部文字，帮你诊断
            if not clicked:
                print("   ⚠️ 未找到底部导航，打印页面文字供诊断:")
                print(page.evaluate("() => document.body.innerText")[:500])
                # 尝试直接点击第三个可见的按钮或 div
                all_clickables = page.locator("button, a, div[role='button'], .van-tabbar-item").all()
                if len(all_clickables) >= 3:
                    all_clickables[2].click()
                    print("   ✅ 已点击第三个可点击元素")
                    clicked = True
            
            page.wait_for_timeout(2000)
            
        except Exception as e:
            print(f"❌ 点击记账中心失败: {e}")
            # 如果失败，打印页面内容供调试
            print(page.evaluate("() => document.body.innerText")[:1000])
            browser.close()
            return
        
        # ---------- 第四步：点击“业绩统计” ----------
        print("📈 进入业绩统计...")
        try:
            # 尝试多种可能的文字
            for text in ["业绩统计", "业绩", "统计", "团队业绩", "数据统计"]:
                try:
                    page.click(f"text={text}")
                    print(f"   ✅ 点击: {text}")
                    page.wait_for_timeout(2000)
                    break
                except:
                    continue
        except Exception as e:
            print(f"⚠️ 业绩统计点击失败: {e}")
        
        # ---------- 第五步：滚动加载 ----------
        print("🔄 滚动加载订单...")
        last_height = 0
        same_count = 0
        while same_count < 3:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                same_count += 1
            else:
                same_count = 0
                last_height = new_height
            print(f"   滚动高度: {new_height}")
        
        # ---------- 第六步：提取数据 ----------
        print("📝 提取订单数据...")
        page_text = page.evaluate("() => document.body.innerText")
        
        orders = []
        # 按“单号”切分
        parts = re.split(r'单号[：:]\s*(\d+)', page_text)
        
        for i in range(1, len(parts), 2):
            order_num = parts[i]
            block_text = parts[i+1] if i+1 < len(parts) else ""
            
            order = {"单号": order_num}
            
            seller = re.search(r'卖家[：:]\s*([^\n]+)', block_text)
            if seller:
                order["卖家"] = seller.group(1).strip()
            
            buyer = re.search(r'买家[：:]\s*([^\n]+)', block_text)
            if buyer:
                order["买家"] = buyer.group(1).strip()
            
            price = re.search(r'价格[：:]\s*(\d+\.?\d*)', block_text)
            if price:
                order["价格"] = float(price.group(1))
            
            profit = re.search(r'收益[：:]\s*(\d+\.?\d*)', block_text)
            if profit:
                order["收益"] = float(profit.group(1))
            
            fee = re.search(r'上架费[：:]\s*(\d+\.?\d*)', block_text)
            if fee:
                order["上架费"] = float(fee.group(1))
            
            time_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', block_text)
            if time_match:
                order["交易时间"] = time_match.group(1)
            
            status_match = re.search(r'(已完成|待付款|待收款|待上架)', block_text)
            if status_match:
                order["状态"] = status_match.group(1)
            
            if order.get("单号"):
                orders.append(order)
        
        print(f"✅ 提取到 {len(orders)} 条订单")
        
        # ---------- 第七步：保存 ----------
        history = []
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                try:
                    history = json.load(f)
                except:
                    history = []
        
        existing_ids = {o.get("单号") for o in history if o.get("单号")}
        new_orders = [o for o in orders if o.get("单号") and o.get("单号") not in existing_ids]
        
        if new_orders:
            history.extend(new_orders)
            print(f"📈 新增 {len(new_orders)} 条，总计 {len(history)} 条")
        else:
            print("📭 没有新订单")
        
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        print(f"💾 数据已保存到 {DATA_FILE}")
        browser.close()

if __name__ == "__main__":
    run_crawler()
