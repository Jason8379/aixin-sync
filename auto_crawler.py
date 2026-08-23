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
        
        # ---------- 第三步：进入记账中心 ----------
        print("📊 点击记账中心...")
        try:
            # 等待底部导航出现
            page.wait_for_selector(".cu-bar.tabbar .action", timeout=15000)
            tabs = page.locator(".cu-bar.tabbar .action").all()
            print(f"   找到 {len(tabs)} 个导航项")
            
            if len(tabs) >= 3:
                tabs[2].click()
                print("   ✅ 点击了记账中心（第三项）")
            else:
                for i, tab in enumerate(tabs):
                    print(f"   导航{i}: {tab.inner_text()}")
                page.click("text=记账中心")
                print("   ✅ 用文本点击记账中心")
            
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"❌ 点击记账中心失败: {e}")
            browser.close()
            return
        
        # ---------- 第四步：点击业绩统计 ----------
        print("📈 进入业绩统计...")
        try:
            # 尝试多种方式
            success = False
            for selector in ["text=业绩统计", "text=业绩", "uni-view:has-text('业绩')"]:
                try:
                    page.click(selector, timeout=5000)
                    print(f"   ✅ 点击成功: {selector}")
                    success = True
                    break
                except:
                    pass
            
            if not success:
                print("   ⚠️ 点击失败，尝试直接滚动到业绩区域")
            
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"⚠️ 业绩统计点击失败: {e}")
        
        # ---------- 第五步：滚动加载 ----------
        print("🔄 滚动加载全部订单...")
        last_height = 0
        same_count = 0
        while same_count < 4:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                same_count += 1
            else:
                same_count = 0
                last_height = new_height
            print(f"   当前高度: {new_height}")
        
        # ---------- 第六步：提取订单 ----------
        print("📝 提取订单数据...")
        orders = []
        box_elements = page.locator(".box").all()
        print(f"   找到 {len(box_elements)} 个订单卡片")
        
        for box in box_elements:
            try:
                text = box.inner_text()
                order_num_match = re.search(r'单号[：:]\s*(\d+)', text)
                if not order_num_match:
                    continue
                
                order = {
                    "单号": order_num_match.group(1),
                    "编号": re.search(r'编号[：:]\s*(\d+)', text).group(1) if re.search(r'编号[：:]\s*(\d+)', text) else "",
                    "卖家": re.search(r'卖家[：:]\s*([^\n]+)', text).group(1).strip() if re.search(r'卖家[：:]\s*([^\n]+)', text) else "",
                    "买家": re.search(r'买家[：:]\s*([^\n]+)', text).group(1).strip() if re.search(r'买家[：:]\s*([^\n]+)', text) else "",
                    "价格": float(re.search(r'价格[：:]\s*(\d+\.?\d*)', text).group(1)) if re.search(r'价格[：:]\s*(\d+\.?\d*)', text) else 0,
                    "收益": float(re.search(r'收益[：:]\s*(\d+\.?\d*)', text).group(1)) if re.search(r'收益[：:]\s*(\d+\.?\d*)', text) else 0,
                    "上架费": float(re.search(r'上架费[：:]\s*(\d+\.?\d*)', text).group(1)) if re.search(r'上架费[：:]\s*(\d+\.?\d*)', text) else 0,
                    "配单时间": re.search(r'配单时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', text).group(1) if re.search(r'配单时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', text) else "",
                    "支付时间": re.search(r'支付时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', text).group(1) if re.search(r'支付时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', text) else "",
                    "状态": re.search(r'(订单完成|待付款|待收款|待上架)', text).group(1) if re.search(r'(订单完成|待付款|待收款|待上架)', text) else "已完成"
                }
                orders.append(order)
            except Exception as e:
                print(f"   ⚠️ 解析失败: {e}")
                continue
        
        print(f"✅ 共提取 {len(orders)} 条订单")
        
        # ---------- 第七步：保存 ----------
        history = []
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                try:
                    history = json.load(f)
                except:
                    history = []
        
        if history and not isinstance(history, list):
            history = []
        
        existing_ids = {o.get("单号") for o in history if o.get("单号")}
        new_orders = [o for o in orders if o.get("单号") and o.get("单号") not in existing_ids]
        
        if new_orders:
            history.extend(new_orders)
            print(f"📈 新增 {len(new_orders)} 条，总计 {len(history)} 条")
        else:
            print("📭 没有新订单")
        
        history.sort(key=lambda x: x.get("配单时间", ""), reverse=True)
        
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        print(f"💾 数据已保存到 {DATA_FILE}")
        browser.close()

if __name__ == "__main__":
    run_crawler()
