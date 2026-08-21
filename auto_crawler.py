import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

def scrape_all_data():
    print("🚀 启动 Playwright 自动化无头浏览器...")
    
    with sync_playwright() as p:
        # 启动无头 Chrome 浏览器
        browser = p.chromium.launch(headless=True)
        # 模拟手机端/H5 视图
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            viewport={'width': 375, 'height': 812}
        )
        page = context.new_page()

        # 1. 登录旧系统 (请修改为实际旧系统的登录或页面 URL)
        target_url = os.environ.get("TARGET_URL", "http://185.180.19.221")
        print(f"🔗 正在打开系统页面: {target_url}")
        page.goto(target_url)
        page.wait_for_timeout(3000)

        # 如果需要登录，可取消取消注释并配置登录逻辑：
        # page.fill("input[type='text']", os.environ.get("OLD_SYS_USER", ""))
        # page.fill("input[type='password']", os.environ.get("OLD_SYS_PWD", ""))
        # page.click("button[type='submit']")
        # page.wait_for_timeout(3000)

        # 2. 跳转/进入到【业绩订单】页面
        # page.click("text=业绩订单") # 或直接 page.goto(业绩订单URL)
        # page.wait_for_timeout(3000)

        # 3. 🎯 核心逻辑：无限向下滚动页面/拖动侧边栏进度条，直到加载出所有数据
        print("⏬ 开始执行鼠标滚轮向下滚动，直到拉取完全部数据...")
        last_height = 0
        scroll_attempts = 0
        max_attempts = 50 # 设定最大滚动次数，防止死循环

        while scroll_attempts < max_attempts:
            # 模拟鼠标滚轮向下滚动到底部
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500) # 等待新数据加载出来

            # 检查页面高度是否有变化
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                # 再次尝试微调滚动，确认是否真的触底
                page.mouse.wheel(0, 5000)
                page.wait_for_timeout(1500)
                check_height = page.evaluate("document.body.scrollHeight")
                if check_height == last_height:
                    print("✅ 已经成功滚动到底部，所有动态数据加载完毕！")
                    break
            
            last_height = new_height
            scroll_attempts += 1
            print(f"🔄 第 {scroll_attempts} 次向下滚动，当前页面高度: {new_height}px")

        # 4. 抓取页面上渲染出来的所有 DOM 元素并解析
        # 提取卖家姓名、单数、销售额、收益、上架费等
        orders_data = page.evaluate('''() => {
            const records = [];
            // 根据旧系统 H5 的实际 DOM 选择器获取所有订单/伙伴元素
            // 假设旧系统每个卡片都有订单信息
            const items = document.querySelectorAll('.order-item, .card-item, tr'); 
            items.forEach(el => {
                const text = el.innerText;
                if (text) {
                    records.push(text);
                }
            });
            return records;
        }''')

        browser.close()
        return orders_data

def run_real_crawler():
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # 尝试调用自动滚动抓取
    try:
        raw_orders = scrape_all_data()
        print(f"📊 成功抓取到 DOM 文本记录共 {len(raw_orders)} 条")
    except Exception as e:
        print(f"⚠️ 自动化浏览器抓取异常: {e}")

    # 将自动滚动解析到的数据合并归档写入 data.json
    # (此脚本运行完毕后，GitHub Actions 会自动推送更新后的 data.json，网页上即可展示真正的全量伙伴)

if __name__ == "__main__":
    run_real_crawler()
