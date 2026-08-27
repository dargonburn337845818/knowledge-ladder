# -*- coding: utf-8 -*-
"""Wallpaper Engine 高清导出工具（NVENC 硬件录制，无需 OBS）

流程：
1. 用 Wallpaper Engine 命令行把壁纸以指定分辨率打开成独立窗口
2. 用 ffmpeg gdigrab 录制该窗口
3. 使用 NVIDIA NVENC (h264_nvenc) 硬件编码，输出高清 MP4
4. 关闭 Wallpaper Engine 窗口

用法（Windows，需要 ffmpeg 带 NVENC 且 NVIDIA 驱动支持）：
    python export_we_wallpaper.py ^
        --wallpaper "D:\\steam\\steamapps\\workshop\\content\\431960\\2898117474\\project.json" ^
        --width 1920 --height 1080 --seconds 15 --output output.mp4
"""

import argparse
import os
import subprocess
import sys
import time

def find_we_exe():
    candidates = [
        r"C:\Program Files (x86)\Steam\steamapps\common\wallpaper_engine\wallpaper32.exe",
        r"C:\Program Files (x86)\Steam\steamapps\common\wallpaper_engine\wallpaper64.exe",
        r"C:\Program Files\Steam\steamapps\common\wallpaper_engine\wallpaper64.exe",
        r"D:\Steam\steamapps\common\wallpaper_engine\wallpaper64.exe",
        r"D:\steam\steamapps\common\wallpaper_engine\wallpaper64.exe",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    # 尝试从 PATH 找
    for exe in ("wallpaper64.exe", "wallpaper32.exe"):
        path = subprocess.run(["where", exe], capture_output=True, text=True)
        if path.returncode == 0 and path.stdout.strip():
            return path.stdout.strip().splitlines()[0]
    return None

def run_we(we_exe, args, check=True):
    cmd = [we_exe, "-control"] + args
    print(">>", " ".join(f'"{x}"' if " " in x else x for x in cmd))
    if check:
        subprocess.run(cmd, check=True)
    else:
        subprocess.run(cmd)

def main():
    ap = argparse.ArgumentParser(description="Wallpaper Engine 高清导出（NVENC）")
    ap.add_argument("--wallpaper", required=True, help="Wallpaper 的 project.json / scene.pkg / 视频文件路径")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--seconds", type=int, default=15)
    ap.add_argument("--framerate", type=int, default=60)
    ap.add_argument("--output", default=os.path.join(r"D:\\wallpaper-vedio", "wallpaper_hd.mp4"))
    ap.add_argument("--window-name", default="WE_HD_Export")
    args = ap.parse_args()

    we_exe = find_we_exe()
    if not we_exe:
        print("错误：找不到 wallpaper32.exe / wallpaper64.exe")
        sys.exit(1)

    if not os.path.isfile(args.wallpaper):
        print(f"错误：壁纸文件不存在：{args.wallpaper}")
        sys.exit(1)

    out_dir = os.path.dirname(os.path.abspath(args.output))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # 打开壁纸窗口
    run_we(we_exe, [
        "openWallpaper",
        "-file", args.wallpaper,
        "-playInWindow", args.window_name,
        "-width", str(args.width),
        "-height", str(args.height),
        "-x", "0", "-y", "0",
    ], check=False)

    print(f"等待 Wallpaper Engine 启动并渲染 3 秒…")
    time.sleep(3)

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "gdigrab",
        "-framerate", str(args.framerate),
        "-i", f"title={args.window_name}",
        "-c:v", "h264_nvenc",
        "-preset", "p5",
        "-t", str(args.seconds),
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        args.output,
    ]
    print(">>", " ".join(ffmpeg_cmd))
    try:
        subprocess.run(ffmpeg_cmd, check=True)
    except FileNotFoundError:
        print("错误：未找到 ffmpeg。请安装带 NVENC 的 ffmpeg，并确保在 PATH 中。")
        run_we(we_exe, ["closeWallpaper", "-location", args.window_name], check=False)
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("错误：ffmpeg 录制失败，可能窗口名未匹配或 NVIDIA NVENC 不可用。")
        run_we(we_exe, ["closeWallpaper", "-location", args.window_name], check=False)
        sys.exit(1)

    # 关闭窗口
    run_we(we_exe, ["closeWallpaper", "-location", args.window_name], check=False)

    print(f"完成：{args.output}（{args.width}x{args.height}，{args.seconds}s，NVENC）")

if __name__ == "__main__":
    main()
