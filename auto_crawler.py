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
    BASE_URL = "https://34.143.196.124/h5"
    TARGET_URL = f"{BASE_URL}/"
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
        try:
            page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"⚠️ 页面加载超时: {e}")
            page.goto(TARGET_URL, wait_until="commit", timeout=60000)
        
        # 强制等待页面渲染
        print("⏳ 等待页面渲染...")
        page.wait_for_timeout(10000)
        
        # ---------- 打印当前页面信息 ----------
        current_url = page.url
        page_title = page.title()
        print(f"📍 当前URL: {current_url}")
        print(f"📄 页面标题: {page_title}")
        
        # 截图保存到仓库（方便诊断）
        screenshot_path = "debug_screenshot.png"
        page.screenshot(path=screenshot_path, full_page=False)
        print(f"📸 已保存截图: {screenshot_path}")
        
        # 获取页面文本内容
        page_text = page.evaluate("() => document.body.innerText")
        print(f"📝 页面文本预览: {page_text[:300]}...")
        
        # ---------- 检查当前是否已经在登录页（没有防火墙） ----------
        if "请输入账号" in page_text or "请输入密码" in page_text:
            print("✅ 已直接进入登录页，无需防火墙认证")
        else:
            # ---------- 处理防火墙 ----------
            print("🛡️ 检测到防火墙页面，开始处理...")
            firewall_success = False
            
            for attempt in range(5):
                try:
                    # 获取所有输入框
                    inputs = page.locator("input").all()
                    visible_inputs = [i for i in inputs if i.is_visible()]
                    print(f"   第 {attempt+1} 次尝试，找到 {len(visible_inputs)} 个可见输入框")
                    
                    # 打印输入框信息
                    for idx, inp in enumerate(visible_inputs):
                        try:
                            placeholder = inp.get_attribute("placeholder") or ""
                            value = inp.get_attribute("value") or ""
                            print(f"      输入框{idx}: placeholder='{placeholder}', value='{value[:10]}'")
                        except:
                            pass
                    
                    if len(visible_inputs) >= 2:
                        # 填写防火墙账号密码
                        visible_inputs[0].click()
                        visible_inputs[0].fill("")
                        visible_inputs[0].fill(FIREWALL_USER)
                        print(f"   ✅ 填了防火墙账号: {FIREWALL_USER}")
                        
                        visible_inputs[1].click()
                        visible_inputs[1].fill("")
                        visible_inputs[1].fill(FIREWALL_PWD)
                        print(f"   ✅ 填了防火墙密码: {FIREWALL_PWD}")
                        
                        # 点击登录按钮
                        login_btn = page.locator("button:has-text('登录')")
                        if login_btn.count() > 0:
                            login_btn.click()
                            print("   ✅ 点击了防火墙'登录'按钮")
                        else:
                            page.keyboard.press("Enter")
                            print("   ✅ 按回车提交")
                        
                        # 等待跳转
                        page.wait_for_timeout(8000)
                        
                        # 检查是否通过防火墙
                        after_text = page.evaluate("() => document.body.innerText")
                        if "请输入账号" in after_text or "请输入密码" in after_text:
                            print("   ✅ 防火墙认证成功，已进入登录页")
                            firewall_success = True
                            break
                        elif "SafeLine" not in after_text and "防火墙" not in after_text:
                            print("   ✅ 防火墙已通过")
                            firewall_success = True
                            break
                        else:
                            print(f"   ⚠️ 防火墙可能未通过，重试...")
                            page.wait_for_timeout(3000)
                    else:
                        print(f"   ⚠️ 输入框数量不足（{len(visible_inputs)}），等待后重试...")
                        page.wait_for_timeout(5000)
                        page.reload()
                        page.wait_for_timeout(5000)
                        
                except Exception as e:
                    print(f"   ⚠️ 防火墙尝试 {attempt+1} 失败: {e}")
                    page.wait_for_timeout(3000)
            
            if not firewall_success:
                print("❌ 防火墙认证失败")
                # 截图保存失败状态
                page.screenshot(path="firewall_failed.png")
                browser.close()
                error_data = {"error": "firewall_failed", "timestamp": time.time()}
                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump(error_data, f, ensure_ascii=False, indent=2)
                return
        
        # ---------- 系统登录 ----------
        print("🔑 开始系统登录...")
        login_success = False
        
        for attempt in range(5):
            try:
                # 等待输入框出现
                page.wait_for_selector("input", timeout=20000)
                inputs = page.locator("input").all()
                visible_inputs = [i for i in inputs if i.is_visible()]
                print(f"   第 {attempt+1} 次尝试，找到 {len(visible_inputs)} 个输入框")
                
                # 打印输入框信息
                for idx, inp in enumerate(visible_inputs):
                    try:
                        placeholder = inp.get_attribute("placeholder") or ""
                        print(f"      输入框{idx}: placeholder='{placeholder}'")
                    except:
                        pass
                
                if len(visible_inputs) >= 3:
                    # 顺序：账号 → 密码 → 店铺号
                    visible_inputs[0].click()
                    visible_inputs[0].fill("")
                    visible_inputs[0].fill(SYS_USER)
                    print(f"   ✅ 填了账号: {SYS_USER}")
                    
                    visible_inputs[1].click()
                    visible_inputs[1].fill("")
                    visible_inputs[1].fill(SYS_PWD)
                    print(f"   ✅ 填了密码: {SYS_PWD}")
                    
                    visible_inputs[2].click()
                    visible_inputs[2].fill("")
                    visible_inputs[2].fill(STORE_NAME)
                    print(f"   ✅ 填了店铺号: {STORE_NAME}")
                elif len(visible_inputs) >= 2:
                    visible_inputs[0].fill(SYS_USER)
                    visible_inputs[1].fill(SYS_PWD)
                    print(f"   ✅ 填了账号+密码")
                else:
                    print(f"   ⚠️ 输入框数量不足，重试...")
                    page.wait_for_timeout(2000)
                    continue
                
                # 点击登录
                login_btn = page.locator("button:has-text('立即登录')")
                if login_btn.count() > 0:
                    login_btn.click()
                    print("   ✅ 点击了'立即登录'按钮")
                else:
                    page.click("text=立即登录")
                    print("   ✅ 用文本点击了'立即登录'")
                
                print("⏳ 等待登录完成...")
                page.wait_for_timeout(12000)
                
                # 验证
                current_url = page.url
                page_text = page.evaluate("() => document.body.innerText")
                
                if "没有账号" in page_text and "立即登录" in page_text:
                    print(f"   ⚠️ 第 {attempt+1} 次登录失败，仍在登录页")
                    page.wait_for_timeout(2000)
                    continue
                else:
                    print(f"✅ 登录成功！当前URL: {current_url}")
                    login_success = True
                    break
                    
            except Exception as e:
                print(f"   ⚠️ 登录尝试 {attempt+1} 失败: {e}")
                page.wait_for_timeout(2000)
        
        if not login_success:
            print("❌ 系统登录失败")
            browser.close()
            error_data = {"error": "login_failed", "timestamp": time.time()}
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(error_data, f, ensure_ascii=False, indent=2)
            return
        
        # ---------- 进入记账中心 ----------
        print("📊 进入记账中心...")
        try:
            page.wait_for_selector(".cu-bar.tabbar .action", timeout=20000)
            tabs = page.locator(".cu-bar.tabbar .action").all()
            print(f"   找到 {len(tabs)} 个导航项")
            if len(tabs) >= 3:
                tabs[2].click()
                print("   ✅ 点击了第三项（记账中心）")
                page.wait_for_timeout(3000)
        except Exception as e:
            print(f"⚠️ 点击导航失败: {e}")
            page.goto(f"{BASE_URL}/#/pages/customer/distribution", wait_until="networkidle")
            page.wait_for_timeout(3000)
        
        # ---------- 采集分销中心汇总数据 ----------
        print("📊 提取分销中心汇总数据...")
        summary_text = page.evaluate("() => document.body.innerText")
        print(f"📝 分销中心文本预览: {summary_text[:200]}...")
        
        summary = {}
        match = re.search(r'可提现佣金[（(]元[）)]?\s*([\d.]+)', summary_text)
        summary["可提现佣金"] = float(match.group(1)) if match else 0.0
        match = re.search(r'已提现佣金[（(]元[）)]?\s*([\d.]+)', summary_text)
        summary["已提现佣金"] = float(match.group(1)) if match else 0.0
        match = re.search(r'推广佣金\s*([\d.]+)', summary_text)
        summary["推广佣金"] = float(match.group(1)) if match else 0.0
        match = re.search(r'推广订单\s*([\d.]+)', summary_text)
        summary["推广订单数"] = int(float(match.group(1))) if match else 0
        match = re.search(r'推荐人[：:]\s*([^\n]+)', summary_text)
        summary["推荐人"] = match.group(1).strip() if match else ""
        match = re.search(r'邀请码[：:]\s*([^\n]+)', summary_text)
        summary["邀请码"] = match.group(1).strip() if match else ""
        print(f"✅ 汇总数据: {summary}")
        
        # ---------- 进入业绩统计 ----------
        print("📈 进入业绩统计...")
        try:
            page.click("text=业绩统计", timeout=5000)
            print("   ✅ 点击了业绩统计")
            page.wait_for_timeout(3000)
        except:
            print("   ⚠️ 点击失败，尝试直接跳转")
            page.goto(f"{BASE_URL}/#/pages/customer/yejitongji", wait_until="networkidle")
            page.wait_for_timeout(3000)
        
        # 滚动加载
        print("🔄 滚动加载订单...")
        last_height = 0
        same_count = 0
        for _ in range(30):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                same_count += 1
                if same_count >= 4:
                    break
            else:
                same_count = 0
                last_height = new_height
            print(f"   滚动高度: {new_height}")
        
        # ---------- 提取订单 ----------
        full_text = page.evaluate("() => document.body.innerText")
        orders = []
        
        print(f"   📊 页面文本长度: {len(full_text)}")
        
        if "业绩订单" not in full_text:
            print("   ⚠️ 未找到'业绩订单'，可能今日无数据")
        else:
            blocks = re.split(r'单号[：:]\s*(\d+)', full_text)
            print(f"   📦 找到 {len(blocks)//2} 个订单块")
            
            for i in range(1, len(blocks), 2):
                order_num = blocks[i]
                block_text = blocks[i+1] if i+1 < len(blocks) else ""
                
                order = {
                    "单号": order_num,
                    "编号": "",
                    "卖家": "",
                    "买家": "",
                    "价格": 0.0,
                    "收益": 0.0,
                    "上架费": 0.0,
                    "配单时间": "",
                    "支付时间": "",
                    "状态": "已完成"
                }
                
                m = re.search(r'编号[：:]\s*(\d+)', block_text)
                if m: order["编号"] = m.group(1)
                
                m = re.search(r'卖家[：:]\s*([^\n]+)', block_text)
                if m:
                    seller = m.group(1).strip()
                    seller = re.sub(r'[^\w\u4e00-\u9fa5]', '', seller)
                    if seller:
                        order["卖家"] = seller
                
                m = re.search(r'买家[：:]\s*([^\n]+)', block_text)
                if m:
                    buyer = m.group(1).strip()
                    buyer = re.sub(r'[^\w\u4e00-\u9fa5]', '', buyer)
                    if buyer:
                        order["买家"] = buyer
                
                m = re.search(r'价格[：:]\s*([\d.]+)', block_text)
                if m: order["价格"] = float(m.group(1))
                
                m = re.search(r'收益[：:]\s*([\d.]+)', block_text)
                if m: order["收益"] = float(m.group(1))
                
                m = re.search(r'上架费[：:]\s*([\d.]+)', block_text)
                if m: order["上架费"] = float(m.group(1))
                
                m = re.search(r'配单时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', block_text)
                if m: order["配单时间"] = m.group(1)
                
                m = re.search(r'支付时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', block_text)
                if m: order["支付时间"] = m.group(1)
                
                m = re.search(r'(订单完成|待付款|待收款|待上架)', block_text)
                if m: order["状态"] = m.group(1)
                
                orders.append(order)
        
        print(f"✅ 提取 {len(orders)} 条订单")
        
        # ---------- 合并历史数据 ----------
        result = {
            "summary": summary,
            "orders": orders,
            "updated_at": datetime.now().isoformat()
        }
        
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                try:
                    old = json.load(f)
                    old_orders = old.get("orders", [])
                    existing_ids = {o.get("单号") for o in old_orders if o.get("单号")}
                    new_orders = [o for o in orders if o.get("单号") and o.get("单号") not in existing_ids]
                    if new_orders:
                        old_orders.extend(new_orders)
                        result["orders"] = old_orders
                        print(f"📈 新增 {len(new_orders)} 条订单")
                except Exception as e:
                    print(f"⚠️ 合并历史数据失败: {e}")
        
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 数据已保存到 {DATA_FILE}")
        print(f"📊 总订单数: {len(result['orders'])}")
        print(f"📊 汇总: {result['summary']}")
        browser.close()

if __name__ == "__main__":
    run_crawler()
