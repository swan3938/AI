#!/usr/bin/env python3
"""每周脑力训练推送：从内容池中按周轮换挑一条，通过 Server酱 推送到微信。

环境变量：
  SERVERCHAN_SENDKEY  —— Server酱的 SendKey（在 GitHub Secrets 里配置，勿硬编码）

可选：
  POOL_DIR            —— 内容池目录，默认 brain-training/pool
  FORCE_INDEX         —— 调试用，强制选择第 N 条（从 0 开始）
"""
import os
import sys
import glob
import datetime
import urllib.parse
import urllib.request


def load_pool(pool_dir):
    files = sorted(glob.glob(os.path.join(pool_dir, "*.md")))
    if not files:
        print(f"内容池为空：{pool_dir}", file=sys.stderr)
        sys.exit(1)
    return files


def pick_file(files):
    force = os.environ.get("FORCE_INDEX")
    if force is not None and force.strip() != "":
        idx = int(force) % len(files)
    else:
        # 按 ISO 周数轮换，保证每周不同、池子循环复用
        week = datetime.date.today().isocalendar()[1]
        idx = week % len(files)
    return files[idx], idx


def split_title_body(path):
    with open(path, encoding="utf-8") as f:
        text = f.read().strip()
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else "脑力训练推送"
    body = "\n".join(lines[1:]).strip()
    return title, body


def send(sendkey, title, body):
    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    data = urllib.parse.urlencode({"title": title, "desp": body}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        out = resp.read().decode("utf-8", "replace")
        print(f"Server酱响应: {out}")
        return out


def main():
    sendkey = os.environ.get("SERVERCHAN_SENDKEY", "").strip()
    if not sendkey:
        print("缺少环境变量 SERVERCHAN_SENDKEY", file=sys.stderr)
        sys.exit(1)

    pool_dir = os.environ.get("POOL_DIR", "brain-training/pool")
    files = load_pool(pool_dir)
    path, idx = pick_file(files)
    title, body = split_title_body(path)
    footer = "\n\n---\n*由 GitHub Actions 每周自动推送 · 想换方向或加内容，随时跟 Claude 说。*"
    print(f"本期选中第 {idx} 条：{os.path.basename(path)}")
    send(sendkey, title, body + footer)


if __name__ == "__main__":
    main()
