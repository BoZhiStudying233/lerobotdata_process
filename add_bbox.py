import pandas as pd
import argparse
import os

def add_bounding_box_columns(csv_path):
    # 读取 CSV 文件
    df = pd.read_csv(csv_path)

    # 添加四个新列，初始值为 0
    df["bbox_x1"] = 0
    df["bbox_y1"] = 0
    df["bbox_x2"] = 0
    df["bbox_y2"] = 0

    # 生成输出路径（避免覆盖原文件）
    dir_name, file_name = os.path.split(csv_path)
    name, ext = os.path.splitext(file_name)
    out_path = os.path.join(dir_name, f"{name}{ext}")

    # 保存新的 CSV 文件
    os.remove(csv_path)
    df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f"✅ 已生成: {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="给 CSV 文件添加 bbox 四列")
    parser.add_argument("--csv_path", type=str, required=True, help="输入 CSV 文件路径")
    args = parser.parse_args()

    add_bounding_box_columns(args.csv_path)
