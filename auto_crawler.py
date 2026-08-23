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
                visible_inputs[0].fill(FIREWALL_USER)
                visible_inputs[1].fill(FIREWALL_PWD)
                page.keyboard.press("Enter")
                print("✅ 防火墙凭证已提交")
                page.wait_for_timeout(5000)
        except Exception as e:
            print(f"⚠️ 防火墙跳过: {e}")
        
        # ---------- 登录 ----------
        print("🔑 登录系统...")
        try:
            page.wait_for_selector("input", timeout=10000)
            inputs = page.locator("input").all()
            visible_inputs = [i for i in inputs if i.is_visible()]
            
            # 打印找到的输入框数量，帮助诊断
            print(f"   找到 {len(visible_inputs)} 个可见输入框")
            
            if len(visible_inputs) >= 3:
                visible_inputs[0].fill(STORE_NAME)  # 店铺名
                visible_inputs[1].fill(SYS_USER)    # 账号
                visible_inputs[2].fill(SYS_PWD)     # 密码
                print("   ✅ 填写了 店铺名 + 账号 + 密码")
            elif len(visible_inputs) >= 2:
                visible_inputs[0].fill(SYS_USER)
                visible_inputs[1].fill(SYS_PWD)
                print("   ✅ 填写了 账号 + 密码")
            
            # 点击登录
            login_btn = page.locator("button:has-text('立即登录')")
            if login_btn.count() > 0:
                login_btn.click()
                print("   ✅ 点击了'立即登录'按钮")
            else:
                page.keyboard.press("Enter")
                print("   ✅ 按回车提交")
            
            print("⏳ 等待登录完成...")
            page.wait_for_timeout(8000)  # 增加等待时间
            
        except Exception as e:
            print(f"❌ 登录失败: {e}")
            browser.close()
            return
        
        # ---------- 验证是否登录成功 ----------
        print("🔍 验证登录状态...")
        page_text = page.evaluate("() => document.body.innerText")
        print(f"   页面文本前200字符: {page_text[:200]}")
        
        # 检查是否还在登录页
        if "立即登录" in page_text and "请输入账号" in page_text:
            print("❌ 登录失败，仍在登录页面")
            browser.close()
            return
        else:
            print("✅ 登录成功，已进入系统")
        
        # ---------- 点击底部导航第三项（记账中心） ----------
        print("📊 点击记账中心...")
        try:
            # 等待底部导航出现（增加超时时间）
            page.wait_for_selector(".cu-bar.tabbar .action", timeout=15000)
            
            # 获取所有导航项
            tabs = page.locator(".cu-bar.tabbar .action").all()
            print(f"   找到 {len(tabs)} 个导航项")
            
            # 打印每个导航的文本
            for i, tab in enumerate(tabs):
                try:
                    text = tab.inner_text()
                    print(f"   导航{i}: {text[:20]}")
                except:
                    print(f"   导航{i}: (无法获取文本)")
            
            if len(tabs) >= 3:
                tabs[2].click()
                print("   ✅ 点击了第三个导航项（记账中心）")
            else:
                # 如果导航项数量不对，尝试点击包含"记账"文字的元素
                page.click("text=记账", timeout=5000)
                print("   ✅ 用'记账'文本点击")
            
            page.wait_for_timeout(4000)
            
        except Exception as e:
            print(f"❌ 点击导航失败: {e}")
            # 打印当前页面内容帮助诊断
            print("=== 当前页面文本 ===")
            print(page.evaluate("() => document.body.innerText")[:500])
            browser.close()
            return
        
        # ---------- 点击“业绩统计” ----------
        print("📈 进入业绩统计...")
        try:
            # 尝试多种方式
            success = False
            for selector in ["text=业绩统计", "text=业绩", "uni-view:has-text('业绩')"]:
                try:
                    page.click(selector, timeout=3000)
                    print(f"   ✅ 点击成功: {selector}")
                    success = True
                    break
                except:
                    pass
            
            if not success:
                # 尝试查找并点击包含"业绩"的元素
                elements = page.locator("uni-view:has-text('业绩')").all()
                if len(elements) > 0:
                    elements[0].click()
                    print("   ✅ 点击了包含'业绩'的元素")
                    success = True
            
            if not success:
                print("   ⚠️ 未找到'业绩统计'，尝试滚动到页面中间")
                page.evaluate("window.scrollTo(0, 300)")
            
            page.wait_for_timeout(3000)
            
        except Exception as e:
            print(f"⚠️ 业绩统计点击失败: {e}")
        
        # 检查当前是否在业绩统计页面
        current_url = page.url
        print(f"📍 当前URL: {current_url}")
        if "yejitongji" in current_url:
            print("✅ 已到达业绩统计页面")
        else:
            print("⚠️ 当前不在业绩统计页面，可能点击未生效")
            # 打印页面文本确认
            print("=== 当前页面文本 ===")
            print(page.evaluate("() => document.body.innerText")[:500])
        
        # ---------- 滚动加载 ----------
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
        
        # ---------- 提取订单 ----------
        print("📝 提取订单数据...")
        orders = []
        
        # 获取页面完整文本
        full_text = page.evaluate("() => document.body.innerText")
        print(f"   页面总文本长度: {len(full_text)}")
        
        # 检查是否有订单数据
        if "单号" in full_text:
            print("   ✅ 页面中包含'单号'")
        else:
            print("   ⚠️ 页面中未找到'单号'")
        
        # 使用 .box 选择器
        box_elements = page.locator(".box").all()
        print(f"   找到 {len(box_elements)} 个 .box 元素")
        
        # 如果 .box 找不到，尝试用正则从文本中提取
        if len(box_elements) == 0:
            print("   🔍 .box 未找到，尝试用正则从文本提取...")
            # 用正则匹配所有订单块
            # 每个订单以"单号："开头
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
        else:
            # 解析 .box 元素
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
                    continue
        
        print(f"✅ 共提取 {len(orders)} 条订单")
        
        # ---------- 保存 ----------
        if orders:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(orders, f, ensure_ascii=False, indent=2)
            print(f"💾 已保存 {len(orders)} 条订单到 {DATA_FILE}")
        else:
            print("⚠️ 未提取到任何订单")
            # 如果页面有内容但没有订单，保留页面内容供分析
            debug_data = {
                "error": "no_orders",
                "timestamp": time.time(),
                "page_text_preview": full_text[:500] if full_text else ""
            }
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)
            print("   已写入调试信息")
        
        browser.close()

if __name__ == "__main__":
    run_crawler()
