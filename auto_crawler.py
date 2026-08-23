import os
import json
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

def run_crawler():
    print("🚀 启动爬虫...")
    
    # 你的登录凭证（已硬编码，不用Secrets也行）
    FIREWALL_USER = "9999"
    FIREWALL_PWD = "8888"
    SYS_USER = "jk1588"
    SYS_PWD = "jk1588"
    STORE_NAME = "XYGDP222222"
    TARGET_URL = "https://185.180.19.221/h5/"
    
    # 数据存储文件
    DATA_FILE = "data.json"
    
    with sync_playwright() as p:
        # 启动无头浏览器（适配GitHub Actions环境）
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
        page.wait_for_timeout(3000)
        
        # ---------- 第一步：防火墙认证 ----------
        print("🛡️ 处理防火墙...")
        try:
            # 等待输入框出现
            page.wait_for_selector("input", timeout=8000)
            inputs = page.locator("input").all()
            visible_inputs = [i for i in inputs if i.is_visible()]
            
            if len(visible_inputs) >= 2:
                visible_inputs[0].fill(FIREWALL_USER)
                visible_inputs[1].fill(FIREWALL_PWD)
                page.keyboard.press("Enter")
                print("✅ 防火墙凭证已提交 (9999/8888)")
                page.wait_for_timeout(5000)
        except Exception as e:
            print(f"⚠️ 防火墙步骤跳过: {e}")
        
        # ---------- 第二步：系统登录 ----------
        print("🔑 登录系统...")
        try:
            page.wait_for_selector("input", timeout=10000)
            inputs = page.locator("input").all()
            visible_inputs = [i for i in inputs if i.is_visible()]
            
            # 根据你截图，三个输入框顺序：店铺名、账号、密码
            if len(visible_inputs) >= 3:
                visible_inputs[0].fill(STORE_NAME)   # 店铺名
                visible_inputs[1].fill(SYS_USER)     # 账号
                visible_inputs[2].fill(SYS_PWD)      # 密码
            elif len(visible_inputs) >= 2:
                visible_inputs[0].fill(SYS_USER)
                visible_inputs[1].fill(SYS_PWD)
            
            # 点击“立即登录”按钮
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
        
        # ---------- 第三步：进入“记账中心” ----------
        print("📊 进入记账中心...")
        try:
            # 尝试点击底部导航第三项
            nav_items = page.locator(".tabbar-item, .van-tabbar-item, nav a, .footer-menu li").all()
            if len(nav_items) >= 3:
                nav_items[2].click()
            else:
                # 备用方案：点击文本
                page.click("text=记账中心")
            page.wait_for_timeout(2000)
        except:
            print("⚠️ 记账中心点击失败，尝试直接点击文本")
            page.click("text=记账中心")
            page.wait_for_timeout(2000)
        
        # ---------- 第四步：点击“业绩统计” ----------
        print("📈 进入业绩统计...")
        try:
            page.click("text=业绩统计")
            page.wait_for_timeout(3000)
        except:
            print("❌ 找不到业绩统计入口")
            browser.close()
            return
        
        # ---------- 第五步：滚动加载所有订单 ----------
        print("🔄 滚动加载全部订单...")
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
            print(f"   当前高度: {new_height}")
        
        # ---------- 第六步：提取订单数据 ----------
        print("📝 提取订单数据...")
        page_text = page.evaluate("() => document.body.innerText")
        
        # 用正则解析每一条订单
        orders = []
        # 匹配模式：单号、卖家、买家、价格、收益、上架费、时间
        # 根据你的截图，每个订单区块包含这些字段
        blocks = re.split(r'单号[：:]\s*(\d+)', page_text)
        
        for i in range(1, len(blocks), 2):
            order_num = blocks[i]
            block_text = blocks[i+1] if i+1 < len(blocks) else ""
            
            order = {"单号": order_num}
            
            # 提取卖家
            seller_match = re.search(r'卖家[：:]\s*([^\n]+)', block_text)
            if seller_match:
                order["卖家"] = seller_match.group(1).strip()
            
            # 提取买家
            buyer_match = re.search(r'买家[：:]\s*([^\n]+)', block_text)
            if buyer_match:
                order["买家"] = buyer_match.group(1).strip()
            
            # 提取价格
            price_match = re.search(r'价格[：:]\s*(\d+\.?\d*)', block_text)
            if price_match:
                order["价格"] = float(price_match.group(1))
            
            # 提取收益
            profit_match = re.search(r'收益[：:]\s*(\d+\.?\d*)', block_text)
            if profit_match:
                order["收益"] = float(profit_match.group(1))
            
            # 提取上架费
            fee_match = re.search(r'上架费[：:]\s*(\d+\.?\d*)', block_text)
            if fee_match:
                order["上架费"] = float(fee_match.group(1))
            
            # 提取时间（配单时间或支付时间）
            time_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', block_text)
            if time_match:
                order["交易时间"] = time_match.group(1)
            
            # 提取状态（已完成/待付款等）
            status_match = re.search(r'(已完成|待付款|待收款|待上架)', block_text)
            if status_match:
                order["状态"] = status_match.group(1)
            
            # 只要有单号就算一条有效数据
            if order.get("单号"):
                orders.append(order)
        
        print(f"✅ 共提取 {len(orders)} 条订单记录")
        
        # ---------- 第七步：保存数据（增量更新） ----------
        # 读取历史数据
        history = []
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                try:
                    history = json.load(f)
                except:
                    history = []
        
        # 用订单号去重
        existing_order_ids = {o.get("单号") for o in history if o.get("单号")}
        new_orders = [o for o in orders if o.get("单号") and o.get("单号") not in existing_order_ids]
        
        if new_orders:
            history.extend(new_orders)
            print(f"📈 新增 {len(new_orders)} 条，总计 {len(history)} 条")
        else:
            print("📭 没有新订单")
        
        # 写入文件
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        print(f"💾 数据已保存到 {DATA_FILE}")
        browser.close()

if __name__ == "__main__":
    run_crawler()
