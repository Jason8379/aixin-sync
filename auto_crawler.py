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
    STATS_URL = "https://185.180.19.221/h5/#/pages/customer/yejitongji"
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
        
        # ---------- 跳转到业绩统计 ----------
        print(f"📈 跳转到业绩统计页面: {STATS_URL}")
        page.goto(STATS_URL, wait_until="networkidle")
        page.wait_for_timeout(10000)  # 增加等待时间
        
        # 打印当前页面信息
        print(f"📍 当前URL: {page.url}")
        print(f"📄 页面标题: {page.title()}")
        
        # 获取页面可见文本（前500字符）
        body_text = page.evaluate("() => document.body.innerText")
        print("=== 页面文本内容（前800字符）===")
        print(body_text[:800])
        print("=== 页面文本结束 ===")
        
        # 检查是否有“总金额”关键字（说明数据已加载）
        if "总金额" in body_text:
            print("✅ 页面中包含'总金额'，数据已加载")
        else:
            print("⚠️ 页面中未找到'总金额'，可能数据未加载或URL不正确")
        
        # ---------- 尝试提取订单 ----------
        print("📝 尝试提取订单...")
        orders = []
        
        # 方法1：使用 .box 选择器
        box_elements = page.locator(".box").all()
        print(f"   方法1 (class='.box'): 找到 {len(box_elements)} 个元素")
        
        # 方法2：如果 .box 找不到，尝试查找包含“单号”的父级元素
        if len(box_elements) == 0:
            # 查找所有包含“单号”文本的元素，然后向上找父级
            order_containers = page.locator("uni-view:has-text('单号')").all()
            print(f"   方法2 (包含'单号'的uni-view): 找到 {len(order_containers)} 个")
            # 将找到的元素视为订单卡片
            for el in order_containers:
                # 尝试获取其父级（可能是整个卡片）
                parent = el.locator("xpath=..")
                if parent.count() > 0:
                    box_elements.append(parent)
        
        # 如果还是没有，尝试查找所有 class 中包含 "box" 的元素
        if len(box_elements) == 0:
            box_elements = page.locator("[class*='box']").all()
            print(f"   方法3 ([class*='box']): 找到 {len(box_elements)} 个")
        
        # 解析每个卡片
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
                print(f"   ⚠️ 解析单个卡片失败: {e}")
                continue
        
        print(f"✅ 共提取 {len(orders)} 条订单")
        
        # ---------- 保存 ----------
        if orders:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(orders, f, ensure_ascii=False, indent=2)
            print(f"💾 已保存 {len(orders)} 条订单到 {DATA_FILE}")
        else:
            print("⚠️ 未提取到任何订单，写入错误标记")
            error_data = {"error": "no_orders", "timestamp": time.time()}
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(error_data, f, ensure_ascii=False, indent=2)
        
        browser.close()

if __name__ == "__main__":
    run_crawler()
