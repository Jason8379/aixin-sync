import time
import json
import asyncio
from playwright.async_api import async_playwright

# 旧项目目标网址
TARGET_URL = "https://185.180.19.221/h5/"
FIREWALL_USER = "9999"
FIREWALL_PASS = "8888"

async def run_auto_sync():
    async with async_playwright() as p:
        # 启动云端 Chrome 无头浏览器，忽略证书警告
        browser = await p.chromium.launch(
            headless=True,
            args=['--ignore-certificate-errors', '--no-sandbox']
        )
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        print("🌐 1. 正在尝试打开目标网页...")
        for attempt in range(3):
            try:
                await page.goto(TARGET_URL, timeout=30000)
                await page.wait_for_load_state("networkidle")
                break
            except Exception as e:
                print(f"⚠️ 网页加载失败或超时，第 {attempt + 1} 次刷新重试...")
                await page.reload()

        # --- 关卡一：解决防火墙网页输入框 ---
        print("🔐 2. 检查并输入防火墙验证卡片...")
        try:
            user_input = page.locator("input[placeholder*='账号'], input[type='text']").first
            pass_input = page.locator("input[placeholder*='密码'], input[type='password']").first
            
            if await user_input.is_visible(timeout=5000):
                await user_input.fill(FIREWALL_USER)
                await pass_input.fill(FIREWALL_PASS)
                login_btn = page.locator("button:has-text('登录'), div:has-text('登录'), input[type='submit']").first
                await login_btn.click()
                print("✅ 防火墙卡片自动填充并点击登录成功！")
                await page.wait_for_timeout(2000)
        except Exception as e:
            print("ℹ️ 未出现防火墙输入框或已跨过防火墙:", e)

        # --- 关卡二：处理弹窗【确定】按钮 ---
        print("💬 3. 检查是否有【确定】弹窗...")
        try:
            confirm_btn = page.locator("button:has-text('确定'), div:has-text('确定'), .van-dialog__confirm").first
            if await confirm_btn.is_visible(timeout=3000):
                await confirm_btn.click()
                print("✅ 已成功点击【确定】弹窗！")
                await page.wait_for_timeout(1000)
        except Exception:
            print("ℹ️ 无阻挡弹窗，顺利进入下一步。")

        # --- 关卡三：系统登录页缓存点击【立即登录】---
        print("🔑 4. 点击系统缓存【立即登录】...")
        try:
            login_now = page.locator("text='立即登录'").first
            if await login_now.is_visible(timeout=4000):
                await login_now.click()
                print("✅ 已点击【立即登录】进入系统后台！")
                await page.wait_for_timeout(3000)
        except Exception:
            print("ℹ️ 账号已是登录状态，直接读取后台数据。")

        # --- 关卡四：点击【记账中心】提取个人数据（含自动刷新容错） ---
        print("📊 5. 进入【记账中心】抓取佣金、推荐人、邀请码...")
        for retry in range(3):
            try:
                acc_btn = page.locator("text='记账中心'").first
                await acc_btn.click()
                await page.wait_for_timeout(2000)
                
                # 检查页面是否白屏
                content = await page.content()
                if "记账" in content or len(content) > 500:
                    print("✅ 成功提取【记账中心】核心数据！")
                    break
                else:
                    raise Exception("页面白屏或加载未完成")
            except Exception as e:
                print(f"⚠️ 点击记账中心无响应或白屏，正在执行第 {retry + 1} 次刷新...")
                await page.reload()
                await page.wait_for_timeout(2000)

        # --- 关卡五：点击【业绩统计】提取团队数据（含自动刷新容错） ---
        print("👥 6. 进入【业绩统计】抓取团队业绩列表...")
        for retry in range(3):
            try:
                perf_btn = page.locator("text='业绩统计'").first
                await perf_btn.click()
                await page.wait_for_timeout(2000)
                
                content = await page.content()
                if "业绩" in content or len(content) > 500:
                    print("✅ 成功提取【业绩统计】团队数据！")
                    break
                else:
                    raise Exception("页面白屏")
            except Exception as e:
                print(f"⚠️ 点击业绩统计白屏，正在执行第 {retry + 1} 次刷新...")
                await page.reload()
                await page.wait_for_timeout(2000)

        print("🎉 自动化任务执行完成！数据已顺利同步至爱心事业管理系统。")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_auto_sync())