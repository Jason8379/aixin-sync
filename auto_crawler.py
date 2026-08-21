name: 爱心事业云端自动抓取同步

on:
  workflow_dispatch:
  schedule:
    - cron: '0 */2 * * *'

permissions:
  contents: write # 显式赋予 GitHub Actions 推送代码和更新文件的权限

jobs:
  build-and-sync:
    runs-on: ubuntu-latest
    steps:
      - name: 检出代码
        uses: actions/checkout@v4 # 升级至 v4 解决 Deprecation 警告

      - name: 设置 Python 环境
        uses: actions/setup-python@v5 # 升级至 v5
        with:
          python-version: '3.10'

      - name: 安装依赖包
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          playwright install chromium --with-deps

      - name: 运行真实遍历爬虫抓取全量数据
        env:
          OLD_SYS_USER: ${{ secrets.OLD_SYS_USER }}
          OLD_SYS_PWD: ${{ secrets.OLD_SYS_PWD }}
          OLD_SYS_URL: ${{ secrets.OLD_SYS_URL }}
        run: |
          python auto_crawler.py

      - name: 提交并推送全量数据到仓库
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add data.json
          git commit -m "Auto-update full team data" || exit 0
          git push origin main
