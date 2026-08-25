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
    TARGET_URL = "https://34.143.196.124/h5/"
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
                print("✅ 防火墙凭证已提交 (9999/8888)")
                page.wait_for_timeout(5000)
        except Exception as e:
            print(f"⚠️ 防火墙步骤跳过: {e}")
        
        # ---------- 系统登录 ----------
        print("🔑 处理系统登录...")
        try:
            page.wait_for_selector("input", timeout=10000)
            inputs = page.locator("input").all()
            visible_inputs = [i for i in inputs if i.is_visible()]
            print(f"   找到 {len(visible_inputs)} 个可见输入框")
            
            if len(visible_inputs) >= 3:
                visible_inputs[0].click()
                visible_inputs[0].fill(SYS_USER)
                print(f"   ✅ 填了账号: {SYS_USER}")
                visible_inputs[1].click()
                visible_inputs[1].fill(SYS_PWD)
                print(f"   ✅ 填了密码: {SYS_PWD}")
                visible_inputs[2].click()
                visible_inputs[2].fill(STORE_NAME)
                print(f"   ✅ 填了店铺号: {STORE_NAME}")
            
            login_btn = page.locator("button:has-text('立即登录')")
            if login_btn.count() > 0:
                login_btn.click()
                print("   ✅ 点击了'立即登录'按钮")
            else:
                page.click("text=立即登录")
                print("   ✅ 用文本点击了'立即登录'")
            
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
        
        if "没有账号" in page_text and "立即登录" in page_text:
            print("❌ 登录失败，仍在登录页面")
            browser.close()
            error_data = {"error": "login_failed", "timestamp": time.time()}
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(error_data, f, ensure_ascii=False, indent=2)
            return
        else:
            print("✅ 登录成功，已进入系统")
        
        # ---------- 进入记账中心 ----------
        print("📊 点击记账中心...")
        try:
            page.wait_for_selector(".cu-bar.tabbar .action", timeout=15000)
            tabs = page.locator(".cu-bar.tabbar .action").all()
            print(f"   找到 {len(tabs)} 个导航项")
            if len(tabs) >= 3:
                tabs[2].click()
                print("   ✅ 点击了第三项（记账中心）")
                page.wait_for_timeout(3000)
        except Exception as e:
            print(f"❌ 点击导航失败: {e}")
            browser.close()
            return
        
        # ---------- 1. 采集业绩统计（订单） ----------
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
        
        # 滚动加载
        print("🔄 滚动加载订单...")
        last_height = 0
        same_count = 0
        for _ in range(20):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                same_count += 1
                if same_count >= 3:
                    break
            else:
                same_count = 0
                last_height = new_height
            print(f"   滚动高度: {new_height}")
        
        # 提取订单
        full_text = page.evaluate("() => document.body.innerText")
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
        print(f"✅ 业绩统计：提取 {len(orders)} 条订单")
        
        # ---------- 2. 采集提现明细 ----------
        print("🏦 进入提现明细...")
        try:
            # 回到记账中心主页（点击返回或重新点击记账中心）
            # 简单方式：直接点击“提现明细”文字
            page.click("text=提现明细", timeout=3000)
            page.wait_for_timeout(3000)
            print("   ✅ 进入提现明细")
        except Exception as e:
            print(f"⚠️ 进入提现明细失败: {e}")
            # 尝试重新从记账中心进入
            page.goto("https://34.143.196.124/h5/#/pages/customer/withdraw", wait_until="networkidle")
            page.wait_for_timeout(3000)
        
        # 滚动加载提现记录
        print("🔄 滚动加载提现记录...")
        for _ in range(10):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)
        
        # 提取提现数据
        withdraw_text = page.evaluate("() => document.body.innerText")
        withdrawals = []
        # 每条提现记录格式：金额 + 日期时间 + 状态（提至提现成功） + 手续费
        # 使用正则匹配
        pattern = r'([\d.]+)\s*元?\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s*手续费：([\d.]+)\s*(提至提现成功|待转账|已打款|失败)'
        matches = re.findall(pattern, withdraw_text)
        for match in matches:
            amount, time_str, fee, status = match
            withdrawals.append({
                "金额": float(amount),
                "时间": time_str,
                "手续费": float(fee),
                "状态": status
            })
        print(f"✅ 提现明细：提取 {len(withdrawals)} 条记录")
        
        # ---------- 3. 采集我的团队 ----------
        print("👥 进入我的团队...")
        try:
            page.click("text=我的团队", timeout=3000)
            page.wait_for_timeout(3000)
            print("   ✅ 进入我的团队")
        except Exception as e:
            print(f"⚠️ 进入我的团队失败: {e}")
            page.goto("https://34.143.196.124/h5/#/pages/customer/myteam", wait_until="networkidle")
            page.wait_for_timeout(3000)
        
        # 滚动加载成员
        print("🔄 滚动加载团队成员...")
        for _ in range(10):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)
        
        team_text = page.evaluate("() => document.body.innerText")
        # 提取汇总数据（团队人数、直推、今日新增、今日总业绩）
        summary = {}
        team_total_match = re.search(r'团队人数[：:]\s*(\d+)', team_text)
        direct_match = re.search(r'直推[：:]\s*(\d+)', team_text)
        today_new_match = re.search(r'今日新增[：:]\s*(\d+)', team_text)
        today_perf_match = re.search(r'今日总业绩[：:]\s*([\d.]+)', team_text)
        summary["team_members"] = int(team_total_match.group(1)) if team_total_match else 0
        summary["direct_referrals"] = int(direct_match.group(1)) if direct_match else 0
        summary["today_new"] = int(today_new_match.group(1)) if today_new_match else 0
        summary["today_total_performance"] = float(today_perf_match.group(1)) if today_perf_match else 0.0
        
        # 提取每个成员（以名字开头，后面跟着今日买入和今日团队业绩）
        members = []
        # 根据截图，每个成员条目格式类似：“宵含\n今日买入：0\n今日团队业绩：0”
        # 使用正则提取
        member_pattern = r'([^\n]+)\n今日买入[：:]\s*([\d.]+)\n今日团队业绩[：:]\s*([\d.]+)'
        member_matches = re.findall(member_pattern, team_text)
        for name, buy, perf in member_matches:
            members.append({
                "昵称": name.strip(),
                "今日买入": float(buy),
                "今日团队业绩": float(perf)
            })
        print(f"✅ 我的团队：提取 {len(members)} 名成员，汇总信息: {summary}")
        
        # ---------- 整合数据 ----------
        result = {
            "orders": orders,
            "withdrawals": withdrawals,
            "team": {
                "summary": summary,
                "members": members
            },
            "updated_at": datetime.now().isoformat()
        }
        
        # 读取历史数据，合并订单（去重）
        history = {}
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                try:
                    history = json.load(f)
                except:
                    history = {}
        
        # 合并订单（用单号去重）
        existing_orders = history.get("orders", [])
        existing_ids = {o.get("单号") for o in existing_orders if o.get("单号")}
        new_orders = [o for o in orders if o.get("单号") and o.get("单号") not in existing_ids]
        if new_orders:
            existing_orders.extend(new_orders)
            print(f"📈 新增 {len(new_orders)} 条订单")
        # 提现和团队直接覆盖（因为它们是历史累计数据，每次全量更新）
        result["orders"] = existing_orders  # 保留历史订单
        # 提现和团队使用最新抓取的结果
        result["withdrawals"] = withdrawals
        result["team"] = {
            "summary": summary,
            "members": members
        }
        
        # 保存
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"💾 数据已保存到 {DATA_FILE}")
        
        browser.close()

if __name__ == "__main__":
    run_crawler()
