import os
import cv2
from natsort import natsorted
import argparse

# 解析命令行参数
parser = argparse.ArgumentParser(description='视频生成脚本，处理图像并生成视频')
parser.add_argument('--root_dir', required=True, help='图像文件的根目录路径')
parser.add_argument('--output_dir', required=True, help='生成视频的输出目录路径')
args = parser.parse_args()

# 从命令行参数获取路径
root_dir = args.root_dir
output_dir = args.output_dir
# # 根目录
# root_dir = r"/data2/konghanlin/internmanip/data/datasets/our_reorganized_data"
# # 输出目录
# output_dir = r"/data2/konghanlin/internmanip/data/datasets/output_small/videos"
os.makedirs(output_dir, exist_ok=True)

episode_counter = 0  # 全局计数器

# 遍历 a 层级 (chunk)
for a_folder in natsorted(os.listdir(root_dir)):
    a_path = os.path.join(root_dir, a_folder)
    if not os.path.isdir(a_path):
        continue
    
    # chunk-00n 文件夹
    chunk_name = f"chunk-{int(a_folder)-1:03d}"
    chunk_output_dir = os.path.join(output_dir, chunk_name)
    os.makedirs(chunk_output_dir, exist_ok=True)
    
    # 遍历 b 层级 (parquet)
    for b_folder in natsorted(os.listdir(a_path)):
        b_path = os.path.join(a_path, b_folder)
        if not os.path.isdir(b_path):
            continue
        
        # 动态读取 b_path 中的文件夹
        c_folders = natsorted([
            folder for folder in os.listdir(b_path)
            if os.path.isdir(os.path.join(b_path, folder))
        ])

        all_images = []
        for c_folder in c_folders:
            c_path = os.path.join(b_path, c_folder, "images", "front")
            if not os.path.exists(c_path):
                continue
            
            # print("c_path:",c_path)
            # 按自然顺序排序图片
            images = natsorted([
                os.path.join(c_path, f)
                for f in os.listdir(c_path)
                if f.lower().endswith((".png", ".jpg"))
            ])
            all_images.extend(images)
        
        if not all_images:
            print(f"跳过空文件夹: {b_path}")
            continue
        
        # 读取第一张图获取视频大小
        first_img = cv2.imread(all_images[0])
        height, width, _ = first_img.shape
        
        # 全局递增命名
        video_name = f"episode_{episode_counter:06d}.mp4"
        folder_name = os.path.basename("video.front")
        folder_path = os.path.join(chunk_output_dir, folder_name)
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        video_path = os.path.join(chunk_output_dir,folder_name,video_name)
        
        # 保存视频
        out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*"mp4v"), 5, (width, height))
        for img_path in all_images:
            img = cv2.imread(img_path)
            out.write(img)
        out.release()
        
        print(f"生成视频: {video_path}")
        episode_counter += 1  # 递增
