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
        # 按一年中的第几天轮换，保证每天不同、池子循环复用
        day = datetime.date.today().timetuple().tm_yday
        idx = day % len(files)
    return files[idx], idx


def split_title_body(path):
    with open(path, encoding="utf-8") as f:
        text = f.read().strip()
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else "脑力训练推送"
    body = "\n".join(lines[1:]).strip()
    return title, body


def clean_for_wechat(body):
    """把 Markdown 转成微信里清爽的纯文本：去掉 # > * ` 等符号，
    列表用「· 」，分隔线变空行，避免在微信预览里显示成乱码般的原始符号。"""
    import re

    out_lines = []
    for raw in body.splitlines():
        line = raw.rstrip()
        # 分隔线 --- *** 直接跳过（用空行替代）
        if re.fullmatch(r"\s*([-*_])\1{2,}\s*", line):
            out_lines.append("")
            continue
        # 去掉标题井号，保留文字
        line = re.sub(r"^\s*#{1,6}\s*", "", line)
        # 去掉引用符号 >
        line = re.sub(r"^\s*>\s?", "", line)
        # 列表符号 - / * 开头 → 「· 」
        line = re.sub(r"^\s*[-*]\s+", "· ", line)
        # 去掉加粗/斜体/行内代码的标记符号，保留内容
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        line = re.sub(r"`(.+?)`", r"\1", line)
        out_lines.append(line)

    # 合并多余空行（最多保留一个）
    text = "\n".join(out_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


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
    body = clean_for_wechat(body)
    footer = "\n\n— — — — —\n每天自动推送 · 想换方向或加内容，跟 Claude 说一声"
    print(f"本期选中第 {idx} 条：{os.path.basename(path)}")
    send(sendkey, title, body + footer)


if __name__ == "__main__":
    main()
