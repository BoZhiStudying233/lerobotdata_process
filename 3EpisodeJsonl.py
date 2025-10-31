#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
生成 episodes.jsonl：
- 每个长程任务 p 对应一个 episode
- 读取对应 q 下的 instruction.txt 作为任务
- length = p/p-1 下所有 data.csv 的行数（去掉标题行）累加
"""

from pathlib import Path
import csv
import json
import os

# # ========== 配置 ==========
# REORG_ROOT = Path("/data2/konghanlin/internmanip/data/datasets/our_reorganized_data")
# OUTPUT_FILE = r"/data2/konghanlin/internmanip/data/datasets/output_small/meta/episodes.jsonl"
# # ========================

import argparse

# 解析命令行参数
parser = argparse.ArgumentParser(description='生成episodes.jsonl文件的脚本')
parser.add_argument('--reorg_root', required=True, help='重组数据的根目录路径')
parser.add_argument('--output_file', required=True, help='生成的episodes.jsonl文件路径')
args = parser.parse_args()

# ========== 配置（从命令行参数读取） ==========
REORG_ROOT = Path(args.reorg_root)
OUTPUT_FILE = args.output_file
# ========================

episode_index = 0
lines = []

# 遍历 q
for q_dir in sorted([p for p in REORG_ROOT.iterdir() if p.is_dir()], key=lambda x: int(x.name)):
    instr_file = q_dir / "instruction.txt"
    if not instr_file.exists():
        print(f"[WARN] {instr_file} 不存在，跳过")
        continue
    with open(instr_file, "r", encoding="utf-8") as f:
        task_instr = f.read().strip()

    # 遍历 p
    for p_dir in sorted([p for p in q_dir.iterdir() if p.is_dir()], key=lambda x: int(x.name)):
        # p-1 下的 data.csv 统计行数
        total_length = 0
        for short_task_dir in sorted([p for p in p_dir.iterdir() if p.is_dir()]):
            data_csv = short_task_dir / "data.csv"
            if not data_csv.exists():
                print(f"[WARN] {data_csv} 不存在，跳过")
                continue
            with open(data_csv, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # 跳过标题行
                count = sum(1 for _ in reader)
                total_length += count

        episode = {
            "episode_index": episode_index,
            "tasks": [task_instr],
            "length": total_length
        }
        lines.append(json.dumps(episode, ensure_ascii=False))
        episode_index += 1

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
# 写入 episodes.jsonl
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"✅ 完成，已生成 {OUTPUT_FILE}，共 {episode_index} 个 episode")
