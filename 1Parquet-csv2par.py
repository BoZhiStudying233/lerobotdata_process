import pandas as pd
import os
import numpy as np

from scipy.spatial.transform import Rotation as R  # 用于四元数和旋转矩阵的转换
import argparse


# ------------------- quaternion 工具 -------------------
def quat_normalize(q):
    q = np.array(q, dtype=float)
    n = np.linalg.norm(q)
    if n == 0:
        return q
    return q / n

def quat_conjugate(q):
    # q assumed as [w, x, y, z]
    w, x, y, z = q
    return np.array([w, -x, -y, -z], dtype=float)

def quat_mul(a, b):
    # Hamilton product, inputs [w, x, y, z]
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    w = aw*bw - ax*bx - ay*by - az*bz
    x = aw*bx + ax*bw + ay*bz - az*by
    y = aw*by - ax*bz + ay*bw + az*bx
    z = aw*bz + ax*by - ay*bx + az*bw
    return np.array([w, x, y, z], dtype=float)

# ------------------- 命令行参数解析 -------------------
def parse_args():
    parser = argparse.ArgumentParser(description='四元数数据处理脚本')
    parser.add_argument('--parent_folder_path', required=True, 
                      help='父文件夹路径')
    parser.add_argument('--output_root', required=True, 
                      help='输出根目录路径')
    return parser.parse_args()


args = parse_args()
parent_folder_path = args.parent_folder_path
output_root = args.output_root

# ------------------- 主流程 -------------------
output_root = os.path.join(output_root, "data")
if not os.path.exists(output_root):
    os.makedirs(output_root)
    print(f"已创建目录: {output_root}")
else:
    print(f"目录已存在: {output_root}")

task_type_folders = sorted(
    [f for f in os.listdir(parent_folder_path) if os.path.isdir(os.path.join(parent_folder_path, f))],
    key=lambda x: int(x)  # 关键：将字符串转换为整数后再排序
)

global_episode_index = 0
global_frame_index = 0
task_index = 0
for type_idx, type_folder in enumerate(task_type_folders):
    type_path = os.path.join(parent_folder_path, type_folder)
    chunk_folder = os.path.join(output_root, f"chunk-{type_idx:03d}")
    os.makedirs(chunk_folder, exist_ok=True)

    task_folders = sorted([f for f in os.listdir(type_path)
                           if os.path.isdir(os.path.join(type_path, f))], key=lambda x: int(x))
    
    
    for task_folder in task_folders:
        

        task_path = os.path.join(type_path, task_folder)
        print("task_path:", task_path)
        # 自动发现子任务文件夹
        subtask_folders = sorted([
            f for f in os.listdir(task_path)
            if os.path.isdir(os.path.join(task_path, f))
        ])
        print("subtask_folders:", subtask_folders)
        all_data = []
        
        # 根据 type_folder 名字是否为奇数来决定 grasp 固定值
        try:
            folder_num = int(type_folder)
        except ValueError:
            # 如果不是纯数字名称，默认设为 False
            folder_num = 0

        # 奇数 -> False，偶数 -> True
        grasp_flag = (folder_num % 2 == 0)

        for folder in subtask_folders:
            grasp = grasp_flag  # 固定为同一个布尔值
            csv_file = os.path.join(task_path, folder, "data.csv")

            if not os.path.exists(csv_file):
                print(f"⚠️ 文件不存在: {csv_file}, 已跳过")
                assert False
                continue
            
            df = pd.read_csv(csv_file)
            # 保证这些列存在并按顺序读取
            required_columns = ["位置X", "位置Y", "位置Z", "姿态X", "姿态Y", "姿态Z", "姿态W",
                        "bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2"]
            # position 保持 [x,y,z]
            required_columns = ["位置X", "位置Y", "位置Z", "姿态X", "姿态Y", "姿态Z", "姿态W"]
            df = df[required_columns]
            df["bbox_x1"] = 0
            df["bbox_y1"] = 0
            df["bbox_x2"] = 0
            df["bbox_y2"] = 0
            
            df["state"] = df[["位置X", "位置Y", "位置Z","姿态X", "姿态Y", "姿态Z", "姿态W"]].values.tolist()
            df["bbox"] = df[["bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2"]].values.tolist()

            # quaternion 保持 [x,y,z,w]
            # df["state.quaternion"] = df[[]].values.tolist()

            # time_offset = df["timestamp"].iloc[-1]
            df["grasp"] = grasp
            df = df[["state","grasp","bbox"]]
            
            all_data.append(df)

        if not all_data:
            print("pass!!!")
            assert False
            continue

        merged_df = pd.concat(all_data, ignore_index=True)

        
        #使得时间从0开始


        # ---------- 归一化（相对于该长程任务的第一帧） ----------
        p0 = np.array(merged_df["state"].iloc[0], dtype=float)
        # q0 = quat_normalize(np.array(merged_df["state.quaternion"].iloc[0], dtype=float))
        # R0 = R.from_quat(q0)  # 初始四元数 -> 旋转矩阵

        norm_states = []
        norm_quats = []

        for pos_list in merged_df["state"]:
            pos = np.array(pos_list, dtype=float)
            # quat = quat_normalize(np.array(quat_list, dtype=float))
            # R_t = R.from_quat(quat)

            rel_pos = (pos - p0).tolist()
            # R_rel = R0.inv() * R_t
            # rel_quat = R_rel.as_quat()  # [x, y, z, w]

            norm_states.append(rel_pos)
            # norm_quats.append(rel_quat.tolist())

        merged_df["state"] = norm_states
        # merged_df["state.quaternion"] = norm_quats

        # 检查第 0 帧四元数
        # first_q = np.array(merged_df["state"].iloc[0], dtype=float)
        # if not np.allclose(first_q, np.array([0.0, 0.0, 0.0, 1.0]), atol=1e-6):
        #     print("⚠️ 注意：第0帧四元数不是精确的单位四元数。")

        # ---------- 新增：action.next_position ----------
        actions = []
        # next_quaternion = []
        for i in range(len(merged_df)):
            if i < len(merged_df) - 1:
                actions.append(merged_df["state"].iloc[i+1])
                # next_quaternion.append(merged_df["state.quaternion"].iloc[i+1])
            else:
                actions.append(merged_df["state"].iloc[i])  # 最后一帧等于自己
                # next_quaternion.append(merged_df["state.quaternion"].iloc[i])
                # next_positions.append([999,888,777])
        merged_df["action"] = actions
        # merged_df["action.next_quaternion"] = next_quaternion
        # ---------- 索引与保存 ----------
        episode_index = global_episode_index
        global_episode_index += 1

        merged_df["frame_index"] = range(len(merged_df))
        merged_df["index"] = range(global_frame_index, global_frame_index + len(merged_df))
        global_frame_index += len(merged_df)
        merged_df["episode_index"] = episode_index
        merged_df["timestamp"] = np.arange(len(merged_df)) * 0.2
        merged_df["task_index"] = task_index
        
        # merged_df["bbox"] = [[0, 0, 0, 0] for _ in range(len(merged_df))]

        # initial_timestamp = merged_df["timestamp"].iloc[0]
        # merged_df["timestamp"] = merged_df["timestamp"] - initial_timestamp

        parquet_file = os.path.join(chunk_folder, f"episode_{episode_index:06d}.parquet")
        merged_df.to_parquet(parquet_file, engine="pyarrow", index=False)

        print(f"✅ 已生成长程任务 {task_folder} 的 parquet 文件: {parquet_file}, 帧数={len(merged_df)}")
        # if parquet_file == "/data3/konghanlin/trans_lerobot_data/output/data/chunk-055/episode_001650.parquet":
        #     assert False
    task_index +=1
