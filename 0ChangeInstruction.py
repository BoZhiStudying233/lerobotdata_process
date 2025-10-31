#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
最终版本：
- 每个长程任务类型 q 下放置 instruction.txt
- 每个短任务 D 拆分为独立的长程任务 p/p-1
- 保留短指令对应关系（按 D 后缀索引）
- 分组 key = Bname + D 后缀（同 B 且同 D 后缀归为同一 q）
"""

from pathlib import Path
import shutil
import re
import argparse
from tqdm import tqdm

# 解析命令行参数
parser = argparse.ArgumentParser(description='数据重组脚本，支持命令行参数指定输入输出路径')
parser.add_argument('--input_root', required=True, help='输入数据根目录路径')
parser.add_argument('--output_train_root', required=True, help='输出数据根目录路径')
# parser.add_argument('--output_test_root', required=True, help='输出数据根目录路径')

args = parser.parse_args()

# ========== 配置（从命令行参数读取） ==========
INPUT_ROOT = Path(args.input_root)
OUTPUT_TRAIN_ROOT = Path(args.output_train_root)
# OUTPUT_TEST_ROOT = Path(args.output_test_root)
alpha = 1  #训练集所占比例


# INPUT_ROOT = Path("/data2/konghanlin/internmanip/data/datasets/our_ori_small")
# OUTPUT_ROOT = Path("/data2/konghanlin/internmanip/data/datasets/our_reorganized_data")
DRY_RUN = False          # True: 只打印计划; False: 实际复制/移动
COPY_MODE = True        # True: 复制(copytree); False: 移动(shutil.move)
# ==================================

import re
from pathlib import Path

def read_type_instruction(b_dir: Path):
    """
    读取 B 目录下的 instruction.txt 并返回内容字符串。
    - 如果存在前缀 '轨迹 n: ...' 或 '轨迹n：...'，则去除该前缀；
    - 不再进行逗号分割等处理。
    """
    instr_file = b_dir / "instruction.txt"
    if not instr_file.exists():
        return ""

    text = instr_file.read_text(encoding="utf-8").strip()
    if not text:
        return ""

    # 去掉 "轨迹 n:" 或 "轨迹n：" 前缀
    text = re.sub(r"^轨迹\s*\d+\s*[:：]\s*", "", text)

    return [text, text]


def make_unique_path(p: Path) -> Path:
    """若路径存在则加后缀 _1/_2/... 返回可用 Path（不创建）"""
    if not p.exists():
        return p
    i = 1
    while True:
        candidate = p.with_name(f"{p.name}_{i}")
        if not candidate.exists():
            return candidate
        i += 1

# 映射： type_key -> q_id ; instance_counter[q_id] -> 已有 p 个数
type_map = {}
type_counter = 0
instance_counter = {}


total_list = sorted([p for p in INPUT_ROOT.iterdir() if p.is_dir()], key=lambda x: x.name)
train_list = total_list[: (int)(alpha*len(total_list))]
test_list = total_list[(int)(alpha*len(total_list))+1:]

print("train_list_length:", len(train_list))
print("test_list_length:", len(test_list))


# OUTPUT_ROOT = OUTPUT_TEST_ROOT
# # 遍历每个 B（种）
# print("在分测试集")
# for b in tqdm(test_list):
#     instr_segments = read_type_instruction(b)  # 短指令列表
#     for c in sorted([p for p in b.iterdir() if p.is_dir()], key=lambda x: x.name):
#         for d in sorted([p for p in c.iterdir() if p.is_dir()], key=lambda x: x.name):
#             suffix = d.name.split("-")[-1]
#             try:
#                 seg_idx = int(suffix) - 1
#             except Exception:
#                 seg_idx = None

#             # 选取对应的短指令
#             short_instr = "（无对应指令）"
#             if seg_idx is not None and 0 <= seg_idx < len(instr_segments):
#                 short_instr = instr_segments[seg_idx]

#             # type_key = Bname + D 后缀
#             type_key = f"{b.name}_{suffix}"
#             if type_key not in type_map:
#                 type_counter += 1
#                 type_map[type_key] = type_counter
#                 instance_counter[type_counter] = 0

#                 # 创建 q 目录并写 instruction.txt（只写一次）
#                 q = type_map[type_key]
#                 q_path = OUTPUT_ROOT / str(q)
#                 if DRY_RUN:
#                     print(f"[DRY_RUN] 创建 q 目录: {q_path}")
#                     print(f"[DRY_RUN] instruction.txt 内容: {short_instr}")
#                 else:
#                     q_path.mkdir(parents=True, exist_ok=True)
#                     instr_file_dst = q_path / "instruction.txt"
#                     if not instr_file_dst.exists():
#                         instr_file_dst.write_text(short_instr + "\n", encoding="utf-8")

#             q = type_map[type_key]
#             instance_counter[q] += 1
#             p = instance_counter[q]

#             # 目标路径： q/p/p-1
#             dst_p_dir = OUTPUT_ROOT / str(q) / str(p)
#             dst_final_d = dst_p_dir / f"{p}-1"
#             if dst_final_d.exists():
#                 dst_final_d = make_unique_path(dst_final_d)

#             # print(f"源 D: {d}")
#             # print(f"  -> 新路径: {dst_final_d}")
#             # print(f"  q={q}  p={p}  指令: {short_instr}\n")

#             if DRY_RUN:
#                 continue

#             # 创建 p 目录
#             dst_p_dir.mkdir(parents=True, exist_ok=True)

#             # 复制或移动短任务
#             if COPY_MODE:
#                 shutil.copytree(d, dst_final_d, dirs_exist_ok=True)
#             else:
#                 shutil.move(str(d), str(dst_final_d))


# 映射： type_key -> q_id ; instance_counter[q_id] -> 已有 p 个数
type_map = {}
type_counter = 0
instance_counter = {}
OUTPUT_ROOT = OUTPUT_TRAIN_ROOT
print("在分训练集")
# 遍历每个 B（种）
for b in tqdm(train_list):
    instr_segments = read_type_instruction(b)  # 短指令列表
    for c in sorted([p for p in b.iterdir() if p.is_dir()], key=lambda x: x.name):
        for d in sorted([p for p in c.iterdir() if p.is_dir()], key=lambda x: x.name):
            suffix = d.name.split("-")[-1]
            try:
                seg_idx = int(suffix) - 1
            except Exception:
                seg_idx = None

            # 选取对应的短指令
            short_instr = "（无对应指令）"
            if seg_idx is not None and 0 <= seg_idx < len(instr_segments):
                short_instr = instr_segments[seg_idx]

            # type_key = Bname + D 后缀
            type_key = f"{b.name}_{suffix}"
            if type_key not in type_map:
                type_counter += 1
                type_map[type_key] = type_counter
                instance_counter[type_counter] = 0

                # 创建 q 目录并写 instruction.txt（只写一次）
                q = type_map[type_key]
                q_path = OUTPUT_ROOT / str(q)
                if DRY_RUN:
                    print(f"[DRY_RUN] 创建 q 目录: {q_path}")
                    print(f"[DRY_RUN] instruction.txt 内容: {short_instr}")
                else:
                    q_path.mkdir(parents=True, exist_ok=True)
                    instr_file_dst = q_path / "instruction.txt"
                    if not instr_file_dst.exists():
                        instr_file_dst.write_text(short_instr + "\n", encoding="utf-8")

            q = type_map[type_key]
            instance_counter[q] += 1
            p = instance_counter[q]

            # 目标路径： q/p/p-1
            dst_p_dir = OUTPUT_ROOT / str(q) / str(p)
            dst_final_d = dst_p_dir / f"{p}-1"
            if dst_final_d.exists():
                dst_final_d = make_unique_path(dst_final_d)

            # print(f"源 D: {d}")
            # print(f"  -> 新路径: {dst_final_d}")
            # print(f"  q={q}  p={p}  指令: {short_instr}\n")

            if DRY_RUN:
                continue

            # 创建 p 目录
            dst_p_dir.mkdir(parents=True, exist_ok=True)

            # 复制或移动短任务
            if COPY_MODE:
                shutil.copytree(d, dst_final_d, dirs_exist_ok=True)
            else:
                shutil.move(str(d), str(dst_final_d))

print("✅ 完成。注意：若 DRY_RUN=True 则未进行实际复制/移动。")
