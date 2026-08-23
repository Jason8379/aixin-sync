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
        
        # ---------- 系统登录 ----------
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
        
        # ---------- 进入“记账中心” ----------
        print("📊 进入记账中心...")
        try:
            # 尝试点击底部导航第三项（常用类名）
            nav_selectors = [
                ".tabbar-item", ".van-tabbar-item", ".bottom-nav a",
                ".footer-menu li", "[role='tab']", ".nav-item"
            ]
            clicked = False
            for selector in nav_selectors:
                items = page.locator(selector).all()
                if len(items) >= 3:
                    items[2].click()
                    clicked = True
                    break
            if not clicked:
                # 尝试点击文本“记账中心”
                page.click("text=记账中心")
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"❌ 点击记账中心失败: {e}")
            browser.close()
            return
        
        # ---------- 点击“业绩统计” ----------
        print("📈 进入业绩统计...")
        try:
            for text in ["业绩统计", "业绩", "统计", "团队业绩"]:
                try:
                    page.click(f"text={text}")
                    print(f"   ✅ 点击: {text}")
                    page.wait_for_timeout(2000)
                    break
                except:
                    continue
        except Exception as e:
            print(f"⚠️ 业绩统计点击失败: {e}")
        
        # ---------- 滚动加载全部订单 ----------
        print("🔄 滚动加载订单（持续直到不再变化）...")
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
        
        # ---------- 提取订单明细 ----------
        print("📝 提取订单数据...")
        # 获取整个页面文本
        page_text = page.evaluate("() => document.body.innerText")
        
        # 用正则按“单号”分割
        orders_raw = []
        # 匹配模式：单号：数字（支持中文冒号）
        parts = re.split(r'单号[：:]\s*(\d+)', page_text)
        # parts[0] 是开头无关文字，之后每两个一组：单号, 内容
        for i in range(1, len(parts), 2):
            order_num = parts[i]
            block_text = parts[i+1] if i+1 < len(parts) else ""
            
            order = {"单号": order_num}
            
            # 提取卖家
            m = re.search(r'卖家[：:]\s*([^\n]+)', block_text)
            if m:
                order["卖家"] = m.group(1).strip()
            
            # 提取买家
            m = re.search(r'买家[：:]\s*([^\n]+)', block_text)
            if m:
                order["买家"] = m.group(1).strip()
            
            # 提取价格（数字，可能带小数点）
            m = re.search(r'价格[：:]\s*(\d+\.?\d*)', block_text)
            if m:
                order["价格"] = float(m.group(1))
            
            # 提取收益
            m = re.search(r'收益[：:]\s*(\d+\.?\d*)', block_text)
            if m:
                order["收益"] = float(m.group(1))
            
            # 提取上架费
            m = re.search(r'上架费[：:]\s*(\d+\.?\d*)', block_text)
            if m:
                order["上架费"] = float(m.group(1))
            
            # 提取配单时间（格式：2026-08-23 02:37:35）
            m = re.search(r'配单时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', block_text)
            if m:
                order["配单时间"] = m.group(1)
            
            # 提取支付时间
            m = re.search(r'支付时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', block_text)
            if m:
                order["支付时间"] = m.group(1)
            
            # 提取状态（已完成/待付款/待收款/待上架）
            m = re.search(r'(已完成|待付款|待收款|待上架)', block_text)
            if m:
                order["状态"] = m.group(1)
            else:
                order["状态"] = "已完成"  # 默认为已完成
            
            # 如果缺少关键字段（价格、收益）也保留，但建议有单号就行
            if order.get("单号"):
                orders_raw.append(order)
        
        print(f"✅ 从页面提取到 {len(orders_raw)} 条订单记录")
        
        # 如果提取不到，打印部分文本供调试
        if not orders_raw:
            print("⚠️ 未提取到任何订单，打印前500字符页面文字以调试：")
            print(page_text[:500])
        
        # ---------- 合并历史数据（去重） ----------
        # 读取历史 data.json
        history = {"orders": []}
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                try:
                    old_data = json.load(f)
                    # 兼容旧格式：如果旧格式是数组，则转为对象包裹
                    if isinstance(old_data, list):
                        history = {"orders": old_data}
                    elif isinstance(old_data, dict) and "orders" in old_data:
                        history = old_data
                    else:
                        # 可能是旧版汇总格式，保留汇总字段，但订单部分新建
                        history = {"orders": []}
                        # 保留汇总字段
                        for key in ["commission", "withdrawable", "withdrawn", "team_sales", "total_orders_count", "shelf_fee_total", "team_members"]:
                            if key in old_data:
                                history[key] = old_data[key]
                except:
                    history = {"orders": []}
        
        # 提取已有订单号集合（用于去重）
        existing_ids = {o.get("单号") for o in history.get("orders", []) if o.get("单号")}
        new_orders = [o for o in orders_raw if o.get("单号") and o.get("单号") not in existing_ids]
        
        if new_orders:
            history["orders"].extend(new_orders)
            print(f"📈 新增 {len(new_orders)} 条订单，总计 {len(history['orders'])} 条")
        else:
            print("📭 没有新订单")
        
        # 更新汇总统计（可选）
        # 计算总收益、总上架费、总金额、人数等
        all_orders = history["orders"]
        total_profit = sum(o.get("收益", 0) for o in all_orders)
        total_fee = sum(o.get("上架费", 0) for o in all_orders)
        total_amount = sum(o.get("价格", 0) for o in all_orders)
        members = set()
        for o in all_orders:
            if o.get("卖家"):
                members.add(o["卖家"])
            if o.get("买家"):
                members.add(o["买家"])
        # 保留原有汇总字段，如果没有则新增
        history["commission"] = history.get("commission", total_profit)  # 如果你希望总收益就是commission，可更新
        history["team_sales"] = history.get("team_sales", total_amount)
        history["total_orders_count"] = len(all_orders)
        history["shelf_fee_total"] = history.get("shelf_fee_total", total_fee)
        history["team_members"] = len(members)
        # 添加日期和用户信息（可选）
        history["date"] = datetime.now().strftime("%Y-%m-%d")
        history["timestamp"] = int(time.time())
        if "user_info" not in history:
            history["user_info"] = {
                "name": "杰克(jk1588)",
                "invite_code": "I2FNPL",
                "referrer": "花长洪"
            }
        
        # 保存
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        print(f"💾 数据已保存到 {DATA_FILE}，总订单数：{len(all_orders)}")
        browser.close()

if __name__ == "__main__":
    run_crawler()
