#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
待办事项提醒程序 - 简易打包脚本
"""

import os
import sys
import subprocess
import shutil

def clean_build():
    """清理之前的构建文件"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"正在删除 {dir_name}...")
            shutil.rmtree(dir_name)

    # 清理Python缓存文件
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))
        if '__pycache__' in dirs:
            shutil.rmtree(os.path.join(root, '__pycache__'))

def build_app():
    """构建应用程序"""
    print("开始构建待办事项提醒程序...")

    # 检查PyInstaller是否安装
    try:
        import PyInstaller
    except ImportError:
        print("错误: 请先安装PyInstaller")
        print("运行: pip install pyinstaller")
        return False

    # 清理旧文件
    clean_build()

    # 执行打包命令
    cmd = ['pyinstaller', 'build.spec']
    print(f"执行命令: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
        print("构建成功!")
        print(result.stdout)

        # 检查输出目录
        dist_dir = os.path.join('dist', '待办事项提醒')
        if os.path.exists(dist_dir):
            print(f"\n构建完成！输出目录: {os.path.abspath(dist_dir)}")
            print("\n主要文件:")
            for file in os.listdir(dist_dir):
                file_path = os.path.join(dist_dir, file)
                size = "文件夹" if os.path.isdir(file_path) else f"{os.path.getsize(file_path)} 字节"
                print(f"  {file} - {size}")

            print(f"\n运行程序: {os.path.join(dist_dir, '待办事项提醒.exe')}")

        return True

    except subprocess.CalledProcessError as e:
        print("构建失败!")
        print("错误信息:", e.stderr)
        return False

def main():
    """主函数"""
    print("=== 待办事项提醒程序打包工具 ===")

    # 检查当前目录
    if not os.path.exists('main.py'):
        print("错误: 请在项目根目录运行此脚本")
        return

    if not os.path.exists('build.spec'):
        print("错误: 找不到 build.spec 文件")
        return

    # 构建应用
    success = build_app()

    if success:
        print("\n✅ 打包完成！")
    else:
        print("\n❌ 打包失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()