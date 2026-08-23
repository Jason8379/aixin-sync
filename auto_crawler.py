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
                print("✅ 防火墙凭证已提交 (9999/8888)")
                page.wait_for_timeout(5000)
            else:
                print("⚠️ 未检测到防火墙输入框，可能已通过防火墙")
        except Exception as e:
            print(f"⚠️ 防火墙步骤跳过: {e}")
        
        # ---------- 第二步：系统登录（智能判断缓存状态） ----------
        print("🔑 处理系统登录...")
        try:
            page.wait_for_selector("input", timeout=10000)
            inputs = page.locator("input").all()
            visible_inputs = [i for i in inputs if i.is_visible()]
            
            print(f"   找到 {len(visible_inputs)} 个可见输入框")
            
            # 打印输入框的当前值，判断是否有缓存
            for i, inp in enumerate(visible_inputs):
                try:
                    val = inp.get_attribute("value") or ""
                    placeholder = inp.get_attribute("placeholder") or ""
                    print(f"   输入框{i}: value='{val[:20]}', placeholder='{placeholder}'")
                except:
                    pass
            
            # 检查第一个输入框是否已有值（缓存）
            first_value = ""
            if len(visible_inputs) >= 1:
                try:
                    first_value = visible_inputs[0].get_attribute("value") or ""
                except:
                    pass
            
            if first_value == SYS_USER:
                # 用户名已缓存，直接点击登录
                print(f"   ✅ 检测到缓存用户名 '{SYS_USER}'，直接点击登录")
                login_btn = page.locator("button:has-text('立即登录')")
                if login_btn.count() > 0:
                    login_btn.click()
                else:
                    page.keyboard.press("Enter")
            else:
                # 输入框为空，填写完整信息
                print("   📝 输入框为空，填写店铺名+账号+密码")
                if len(visible_inputs) >= 3:
                    visible_inputs[0].fill(STORE_NAME)
                    visible_inputs[1].fill(SYS_USER)
                    visible_inputs[2].fill(SYS_PWD)
                    print(f"   ✅ 已填写: 店铺名={STORE_NAME}, 账号={SYS_USER}")
                elif len(visible_inputs) >= 2:
                    visible_inputs[0].fill(SYS_USER)
                    visible_inputs[1].fill(SYS_PWD)
                    print(f"   ✅ 已填写: 账号={SYS_USER}")
                
                # 点击登录
                login_btn = page.locator("button:has-text('立即登录')")
                if login_btn.count() > 0:
                    login_btn.click()
                else:
                    page.keyboard.press("Enter")
            
            print("⏳ 等待登录完成...")
            page.wait_for_timeout(8000)
            
        except Exception as e:
            print(f"❌ 登录操作失败: {e}")
            browser.close()
            return
        
        # ---------- 第三步：验证登录是否成功 ----------
        print("🔍 验证登录状态...")
        current_url = page.url
        page_text = page.evaluate("() => document.body.innerText")
        print(f"   当前URL: {current_url}")
        
        # 判断是否在登录页（如果同时包含"立即登录"和"没有账号"则仍在登录页）
        if "没有账号" in page_text and "立即登录" in page_text:
            print("❌ 登录失败，仍在登录页面")
            print("=== 页面内容 ===")
            print(page_text[:500])
            browser.close()
            error_data = {"error": "login_failed", "timestamp": time.time(), "url": current_url}
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(error_data, f, ensure_ascii=False, indent=2)
            return
        else:
            print("✅ 登录成功，已进入系统")
        
        # ---------- 第四步：进入记账中心（底部导航第三项） ----------
        print("📊 点击记账中心...")
        try:
            # 等待底部导航出现
            page.wait_for_selector(".cu-bar.tabbar .action", timeout=15000)
            tabs = page.locator(".cu-bar.tabbar .action").all()
            print(f"   找到 {len(tabs)} 个导航项")
            
            # 打印导航文本
            for i, tab in enumerate(tabs):
                try:
                    text = tab.inner_text()
                    print(f"   导航{i}: {text[:30]}")
                except:
                    pass
            
            if len(tabs) >= 3:
                tabs[2].click()
                print("   ✅ 点击了第三项（记账中心）")
                page.wait_for_timeout(3000)
            else:
                # 如果导航项数量不够，尝试点击包含"记账"的元素
                page.click("text=记账", timeout=5000)
                print("   ✅ 用'记账'文本点击")
                page.wait_for_timeout(3000)
            
        except Exception as e:
            print(f"❌ 点击导航失败: {e}")
            print("=== 当前页面内容 ===")
            print(page.evaluate("() => document.body.innerText")[:500])
            browser.close()
            return
        
        # ---------- 第五步：点击业绩统计 ----------
        print("📈 进入业绩统计...")
        try:
            # 尝试多种方式
            for selector in ["text=业绩统计", "text=业绩", "uni-view:has-text('业绩')"]:
                try:
                    page.click(selector, timeout=3000)
                    print(f"   ✅ 点击成功: {selector}")
                    page.wait_for_timeout(3000)
                    break
                except:
                    continue
        except Exception as e:
            print(f"⚠️ 业绩统计点击失败: {e}")
        
        print(f"📍 当前URL: {page.url}")
        
        # ---------- 第六步：滚动加载 ----------
        print("🔄 滚动加载全部订单...")
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
        
        # ---------- 第七步：提取订单 ----------
        print("📝 提取订单数据...")
        full_text = page.evaluate("() => document.body.innerText")
        print(f"   页面总文本长度: {len(full_text)}")
        
        orders = []
        # 用正则分割订单
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
        
        # ---------- 保存 ----------
        if orders:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(orders, f, ensure_ascii=False, indent=2)
            print(f"💾 已保存 {len(orders)} 条订单")
        else:
            # 如果有页面内容但没有订单，保存预览用于调试
            debug_data = {
                "error": "no_orders", 
                "timestamp": time.time(), 
                "page_preview": full_text[:500] if len(full_text) > 0 else "empty",
                "url": page.url
            }
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)
            print("⚠️ 未提取到订单，已写入调试信息")
        
        browser.close()

if __name__ == "__main__":
    run_crawler()
