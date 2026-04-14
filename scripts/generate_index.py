#!/usr/bin/env python3
"""Generate index.html listing all bipolar disorder daily reports."""

import glob
import os
from datetime import datetime

html_files = sorted(glob.glob("docs/bipolar-*.html"), reverse=True)
links = ""
for f in html_files[:30]:
    name = os.path.basename(f)
    date = name.replace("bipolar-", "").replace(".html", "")
    try:
        d = datetime.strptime(date, "%Y-%m-%d")
        date_display = d.strftime("%Y年%-m月%-d日")
    except Exception:
        date_display = date
    weekday = (
        ["一", "二", "三", "四", "五", "六", "日"][
            datetime.strptime(date, "%Y-%m-%d").weekday()
        ]
        if len(date) == 10
        else ""
    )
    links += f'<li><a href="{name}">📅 {date_display}（週{weekday}）</a></li>\n'

total = len(html_files)

index = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Bipolar Brain · 雙相情緒障礙症文獻日報</title>
<style>
  :root {{ --bg: #f0f4f8; --surface: #ffffff; --line: #d0dbe8; --text: #1a2a3a; --muted: #5a6a7a; --accent: #2563eb; --accent-soft: #dbeafe; }}
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: linear-gradient(135deg, #f0f4f8 0%, #e8f0fe 50%, #f0f4f8 100%); color: var(--text); font-family: "Noto Sans TC", "PingFang TC", "Helvetica Neue", Arial, sans-serif; min-height: 100vh; }}
  .container {{ position: relative; z-index: 1; max-width: 640px; margin: 0 auto; padding: 80px 24px; }}
  .logo {{ font-size: 48px; text-align: center; margin-bottom: 16px; }}
  h1 {{ text-align: center; font-size: 24px; color: var(--text); margin-bottom: 8px; }}
  .subtitle {{ text-align: center; color: var(--accent); font-size: 14px; margin-bottom: 48px; }}
  .count {{ text-align: center; color: var(--muted); font-size: 13px; margin-bottom: 32px; }}
  ul {{ list-style: none; }}
  li {{ margin-bottom: 8px; }}
  a {{ color: var(--text); text-decoration: none; display: block; padding: 14px 20px; background: var(--surface); border: 1px solid var(--line); border-radius: 12px; transition: all 0.2s; font-size: 15px; }}
  a:hover {{ background: var(--accent-soft); border-color: var(--accent); transform: translateX(4px); }}
  footer {{ margin-top: 56px; text-align: center; font-size: 12px; color: var(--muted); }}
  footer a {{ display: inline; padding: 0; background: none; border: none; color: var(--muted); }}
  footer a:hover {{ color: var(--accent); }}
</style>
</head>
<body>
<div class="container">
  <div class="logo">🧠</div>
  <h1>Bipolar Brain</h1>
  <p class="subtitle">雙相情緒障礙症文獻日報 · 每日自動更新</p>
  <p class="count">共 {total} 期日報</p>
  <ul>{links}</ul>
  <footer>
    <p>Powered by PubMed + Zhipu AI · <a href="https://github.com/u8901006/bipolar-brain">GitHub</a></p>
    <p style="margin-top:8px"><a href="https://www.leepsyclinic.com/" target="_blank">🏥 李政洋身心診所</a> · <a href="https://blog.leepsyclinic.com/" target="_blank">📬 訂閱電子報</a></p>
  </footer>
</div>
</body>
</html>"""

with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(index)
print("Index page generated")
