#!/usr/bin/env python3
"""每日脑力训练：调用 Claude 生成一条全新内容 → 归档 → 推送到微信。

环境变量：
  ANTHROPIC_API_KEY   Claude API 密钥（GitHub Secret）
  SERVERCHAN_SENDKEY  Server酱 SendKey（GitHub Secret，兼容 SEND）
  GEN_MODEL           生成模型，默认 claude-sonnet-4-6
若没有 ANTHROPIC_API_KEY 或生成失败，自动回退到 brain-training/pool 轮换，保证推送不中断。
"""
import os
import sys
import re
import glob
import json
import datetime
import urllib.parse
import urllib.request

POOL_DIR = os.environ.get("POOL_DIR", "brain-training/pool")
ARCHIVE_DIR = os.environ.get("ARCHIVE_DIR", "brain-training/archive")
MODEL = os.environ.get("GEN_MODEL", "claude-sonnet-4-6")
CATEGORIES = ["动脑题", "训练法", "练脑游戏", "思维技巧"]


# ---------- 通用工具 ----------
def split_title_body(text):
    text = text.strip()
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else "脑力训练"
    body = "\n".join(lines[1:]).strip()
    return title, body


def clean_for_wechat(body):
    """把 Markdown 转成微信里清爽的纯文本。"""
    out = []
    for raw in body.splitlines():
        line = raw.rstrip()
        if re.fullmatch(r"\s*([-*_])\1{2,}\s*", line):
            out.append("")
            continue
        line = re.sub(r"^\s*#{1,6}\s*", "", line)
        line = re.sub(r"^\s*>\s?", "", line)
        line = re.sub(r"^\s*[-*]\s+", "· ", line)
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        line = re.sub(r"`(.+?)`", r"\1", line)
        out.append(line)
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(out))
    return text.strip()


def existing_titles():
    titles = []
    for d in (POOL_DIR, ARCHIVE_DIR):
        for f in sorted(glob.glob(os.path.join(d, "*.md"))):
            try:
                with open(f, encoding="utf-8") as fh:
                    first = fh.readline().lstrip("# ").strip()
                if first:
                    titles.append(first)
            except OSError:
                pass
    return titles


# ---------- 推送 ----------
def send(sendkey, title, body):
    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    data = urllib.parse.urlencode({"title": title, "desp": body}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        print("Server酱响应:", resp.read().decode("utf-8", "replace"))


# ---------- 生成 ----------
def generate(api_key, category, avoid):
    avoid_text = "\n".join("- " + t for t in avoid) or "（暂无）"
    system = (
        "你为'每日脑力训练'微信推送生成内容。用简体中文。核心要求：内容必须真正"
        "锻炼大脑——让人当天动手去做、去解、去练，而不是只读一个概念长见识。"
        "语言通俗有力，有具体例子，拒绝空泛和陈词滥调。"
    )
    user = f"""今天生成的类型是：{category}。请生成一条全新的「{category}」脑力训练内容。

严格按以下格式输出（只输出内容本身，不要解释、不要用代码块包裹）：
第一行：# <一个emoji> {category} · <简短有吸引力的标题>
然后正文，包含：
1) 用通俗有力的话讲清它（钩子/原理/为什么值得练）；
2) 一段以「🎯 今日任务：」开头、当天就能动手完成的具体练习；
3) 一段以「📚」开头的延伸来源，必须是真实存在的具体书/网站/工具/人名。
如果类型是「动脑题」，再额外加：一行以「💡 提示：」开头的思路提示，以及一段用「———（先想，再看）———」分隔的解法。
总长约 250–400 字。题目要有真正的难度和趣味，避免三门问题、囚徒困境这类被讲烂的老梗。

不要与以下已经用过的主题重复或近义：
{avoid_text}"""

    body = json.dumps({
        "model": MODEL,
        "max_tokens": 1600,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }).encode("utf-8")
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, method="POST")
    req.add_header("x-api-key", api_key)
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("content-type", "application/json")
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    text = "".join(part.get("text", "") for part in data.get("content", [])).strip()
    text = re.sub(r"^```[a-z]*\n?|\n?```$", "", text).strip()  # 去掉可能的代码块包裹
    if not text or not text.startswith("#"):
        raise ValueError(f"生成结果格式异常: {text[:120]!r}")
    return text


def fallback_from_pool():
    files = sorted(glob.glob(os.path.join(POOL_DIR, "*.md")))
    if not files:
        print("内容池为空，无法回退", file=sys.stderr)
        sys.exit(1)
    idx = datetime.date.today().timetuple().tm_yday % len(files)
    with open(files[idx], encoding="utf-8") as f:
        print(f"回退使用内容池：{os.path.basename(files[idx])}")
        return f.read()


def main():
    sendkey = (os.environ.get("SERVERCHAN_SENDKEY") or "").strip()
    if not sendkey:
        print("缺少 SERVERCHAN_SENDKEY", file=sys.stderr)
        sys.exit(1)

    api_key = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    today = datetime.date.today()
    category = CATEGORIES[today.toordinal() % len(CATEGORIES)]
    content = None

    if api_key:
        try:
            content = generate(api_key, category, existing_titles())
            os.makedirs(ARCHIVE_DIR, exist_ok=True)
            title_line = content.splitlines()[0].lstrip("# ").strip()
            safe = re.sub(r"[^\w一-龥]+", "-", title_line)[:40].strip("-")
            path = os.path.join(ARCHIVE_DIR, f"{today.isoformat()}-{safe}.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content + "\n")
            print(f"已生成并归档：{path}")
        except Exception as e:  # 生成失败不能让推送中断
            print(f"生成失败，回退内容池：{e}", file=sys.stderr)
            content = None
    else:
        print("未配置 ANTHROPIC_API_KEY，使用内容池轮换")

    if content is None:
        content = fallback_from_pool()

    title, body = split_title_body(content)
    footer = "\n\n— — — — —\n每天自动推送 · 想换方向或调整，跟 Claude 说一声"
    send(sendkey, title, clean_for_wechat(body) + footer)


if __name__ == "__main__":
    main()
