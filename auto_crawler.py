import json
import os
import time
from datetime import datetime

def run_crawler_and_save():
    print("🚀 开始执行爱心事业云端自动抓取程序...")
    
    # -------------------------------------------------------------
    # 1. 模拟抓取旧项目数据（这里放置抓取逻辑，提取佣金和团队数据）
    # -------------------------------------------------------------
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # 假设抓取到的数据结构（替换为实际抓取变量）：
    new_data_point = {
        "date": today_str,
        "timestamp": int(time.time()),
        "commission": 1280.50,  # 抓到的今日累计佣金
        "team_members": 42,      # 抓到的团队总人数
        "team_sales": 15600.00   # 抓到的团队总业绩
    }
    
    # -------------------------------------------------------------
    # 2. 读取已有的历史账本文件 (data.json)
    # -------------------------------------------------------------
    json_file = "data.json"
    history_records = []
    
    if os.path.exists(json_file):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                history_records = json.load(f)
                print(f"📖 成功读取现有账本，共 {len(history_records)} 条历史记录")
        except Exception as e:
            print(f"⚠️ 读取历史账本失败，准备新建: {e}")
            history_records = []

    # -------------------------------------------------------------
    # 3. 追加/更新今天的记录（按日期去重，保留最新抓取）
    # -------------------------------------------------------------
    # 过滤掉同日期的旧记录
    updated_records = [item for item in history_records if item.get("date") != today_str]
    # 追加今天的最新数据
    updated_records.append(new_data_point)
    
    # 按日期排序
    updated_records.sort(key=lambda x: x.get("date", ""))

    # -------------------------------------------------------------
    # 4. 重新写入 data.json 文件
    # -------------------------------------------------------------
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(updated_records, f, ensure_ascii=False, indent=2)
        
    print(f"✅ {today_str} 的数据已成功追加写入云端账本 (data.json)！")

if __name__ == "__main__":
    run_crawler_and_save()
