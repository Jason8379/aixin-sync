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
        
        print(f"🌐 访问登录页: {TARGET_URL}")
        page.goto(TARGET_URL, wait_until="networkidle")
        page.wait_for_timeout(4000)
        
        # ---------- 防火墙 ----------
        print("🛡️ 处理防火墙...")
        try:
            page.wait_for_selector("input", timeout=8000)
            inputs = page.locator("input").all()
            visible_inputs = [i for i in inputs if i.is_visible()]
            if len(visible_inputs) >= 2:
                visible_inputs[0].click()
                visible_inputs[0].fill(FIREWALL_USER)
                visible_inputs[1].click()
                visible_inputs[1].fill(FIREWALL_PWD)
                # 点击防火墙登录按钮
                login_btn = page.locator("button:has-text('登录')")
                if login_btn.count() > 0:
                    login_btn.click()
                else:
                    page.keyboard.press("Enter")
                print("✅ 防火墙凭证已提交")
                page.wait_for_timeout(6000)
        except Exception as e:
            print(f"⚠️ 防火墙跳过: {e}")
        
        # ---------- 系统登录 ----------
        print("🔑 处理系统登录...")
        try:
            # 等待输入框出现
            page.wait_for_selector("input", timeout=15000)
            inputs = page.locator("input").all()
            visible_inputs = [i for i in inputs if i.is_visible()]
            print(f"   找到 {len(visible_inputs)} 个可见输入框")
            
            # 方法：先点击输入框再填值（模拟真实用户操作）
            if len(visible_inputs) >= 3:
                # 账号
                visible_inputs[0].click()
                visible_inputs[0].fill(SYS_USER)
                print(f"   ✅ 填了账号: {SYS_USER}")
                
                # 密码
                visible_inputs[1].click()
                visible_inputs[1].fill(SYS_PWD)
                print(f"   ✅ 填了密码: {SYS_PWD}")
                
                # 店铺号
                visible_inputs[2].click()
                visible_inputs[2].fill(STORE_NAME)
                print(f"   ✅ 填了店铺号: {STORE_NAME}")
                
                # 关键：点击页面其他地方让输入框失焦（触发验证）
                page.click("text=立即登录", timeout=1000).catch(lambda: None)
                page.wait_for_timeout(1000)
            
            # 用鼠标点击"立即登录"按钮（而不是按回车）
            login_btn = page.locator("button:has-text('立即登录')")
            if login_btn.count() > 0:
                login_btn.click()
                print("   ✅ 点击了'立即登录'按钮")
            else:
                # 尝试用 JavaScript 触发点击
                page.evaluate("document.querySelector('button:has-text(立即登录)')?.click()")
                print("   ✅ 用JS点击了登录按钮")
            
            print("⏳ 等待登录完成...")
            page.wait_for_timeout(10000)
            
        except Exception as e:
            print(f"❌ 登录操作失败: {e}")
            browser.close()
            return
        
        # ---------- 验证登录 ----------
        print("🔍 验证登录状态...")
        current_url = page.url
        page_text = page.evaluate("() => document.body.innerText")
        print(f"   当前URL: {current_url}")
        
        # 检查是否还在登录页
        if "没有账号" in page_text and "立即登录" in page_text:
            print("❌ 登录失败，仍在登录页面")
            print("=== 页面内容 ===")
            print(page_text[:500])
            
            # 额外：检查是否有错误提示
            print("\n=== 尝试查找错误信息 ===")
            error_msgs = page.locator(".error, .tip, .toast, .message").all()
            for err in error_msgs:
                try:
                    print(f"   错误提示: {err.inner_text()}")
                except:
                    pass
            
            browser.close()
            error_data = {"error": "login_failed", "timestamp": time.time(), "url": current_url}
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(error_data, f, ensure_ascii=False, indent=2)
            return
        else:
            print("✅ 登录成功！")
        
        # ---------- 后续步骤 ----------
        print("📊 点击记账中心...")
        try:
            page.wait_for_selector(".cu-bar.tabbar .action", timeout=15000)
            tabs = page.locator(".cu-bar.tabbar .action").all()
            print(f"   找到 {len(tabs)} 个导航项")
            if len(tabs) >= 3:
                tabs[2].click()
                print("   ✅ 点击了第三项")
                page.wait_for_timeout(3000)
        except Exception as e:
            print(f"❌ 点击导航失败: {e}")
            browser.close()
            return
        
        print("📈 进入业绩统计...")
        try:
            for selector in ["text=业绩统计", "text=业绩"]:
                try:
                    page.click(selector, timeout=3000)
                    print(f"   ✅ 点击成功: {selector}")
                    page.wait_for_timeout(3000)
                    break
                except:
                    continue
        except Exception as e:
            print(f"⚠️ 点击失败: {e}")
        
        # ---------- 滚动加载 ----------
        print("🔄 滚动加载...")
        last_height = 0
        same_count = 0
        scroll_rounds = 0
        while same_count < 4 and scroll_rounds < 20:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                same_count += 1
            else:
                same_count = 0
                last_height = new_height
            scroll_rounds += 1
            print(f"   滚动 {scroll_rounds}: 高度 {new_height}")
        
        # ---------- 提取订单 ----------
        print("📝 提取订单...")
        full_text = page.evaluate("() => document.body.innerText")
        print(f"   页面长度: {len(full_text)}")
        
        orders = []
        blocks = re.split(r'单号[：:]\s*(\d+)', full_text)
        for i in range(1, len(blocks), 2):
            order_num = blocks[i]
            block_text = blocks[i+1] if i+1 < len(blocks) else ""
            order = {
                "单号": order_num,
                "编号": re.search(r'编号[：:]\s*(\d+)', block_text).group(1) if re.search(r'编号[：:]\s*(\d+)', block_text) else "",
                "卖家": re.search(r'卖家[：:]\s*([^\n]+)', block_text).group(1).strip() if re.search(r'卖家[：:]\s*([^\n]+)', block_text) else "",
                "买家": re.search(r'买家[：:]\s*([^\n]+)', block_text).group(1).strip() if re.search(r'买家[：:]\s*([^\n]+)', block_text) else "",
                "价格": float(re.search(r'价格[：:]\s*(\d+\.?\d*)', block_text).group(1)) if re.search(r'价格[：:]\s*(\d+\.?\d*)', block_text) else 0,
                "收益": float(re.search(r'收益[：:]\s*(\d+\.?\d*)', block_text).group(1)) if re.search(r'收益[：:]\s*(\d+\.?\d*)', block_text) else 0,
                "上架费": float(re.search(r'上架费[：:]\s*(\d+\.?\d*)', block_text).group(1)) if re.search(r'上架费[：:]\s*(\d+\.?\d*)', block_text) else 0,
                "配单时间": re.search(r'配单时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', block_text).group(1) if re.search(r'配单时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', block_text) else "",
                "支付时间": re.search(r'支付时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', block_text).group(1) if re.search(r'支付时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', block_text) else "",
                "状态": re.search(r'(订单完成|待付款|待收款|待上架)', block_text).group(1) if re.search(r'(订单完成|待付款|待收款|待上架)', block_text) else "已完成"
            }
            orders.append(order)
        
        print(f"✅ 共提取 {len(orders)} 条订单")
        
        if orders:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(orders, f, ensure_ascii=False, indent=2)
            print(f"💾 已保存")
        else:
            debug_data = {
                "error": "no_orders",
                "timestamp": time.time(),
                "page_preview": full_text[:500]
            }
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)
            print("⚠️ 未提取到订单")
        
        browser.close()

if __name__ == "__main__":
    run_crawler()
