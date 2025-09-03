import datetime

from screeninfo import get_monitors
import os
import subprocess
from win32api import GetSystemMetrics
from time import sleep
from sys import exit


import psutil
import shutil

# 应用进程名字（列表）
PROCESS_NAME = "DesktopMgr"
# appdata路径
APP_DATA_PATH = os.getenv("APPDATA") + "\\Tencent\\DeskGo"
# 备份文件的根目录
BACKUP_PATH = APP_DATA_PATH + "\\Backup"
# 数据名字列表
DATA_NAME_LIST = ["ConFile.dat", "DesktopMgr.lg", "FencesDataFile.dat"]

# 屏幕列表
screen_list = []
# 实际屏幕分辨率（经过缩放）
screen_real_width = 0
screen_real_height = 0

# 根据当前屏幕状态获取的备份文件名
backup_folder_name = ''
# 完整的备份文件路径
backup_folder_path = ''


def init():
    global screen_real_width, screen_real_height, backup_folder_name, backup_folder_path

    screen_real_width = GetSystemMetrics(78)
    screen_real_height = GetSystemMetrics(79)
    screen_list.extend(get_monitors())
    backup_folder_name = get_backup_folder_name_by_current_screen()
    backup_folder_path = BACKUP_PATH + "\\" + backup_folder_name


def get_backup_folder_name_by_current_screen():
    primary_screen = [screen for screen in screen_list if screen.is_primary][0]
    backup_folder_name = primary_screen.name.replace('\\\\.\\', '')
    for screen in screen_list:
        if screen.is_primary:
            continue
        backup_folder_name += '-' + screen.name.replace('\\\\.\\', '') + '&'
    if len(screen_list) > 1:
        backup_folder_name = backup_folder_name[:-1]

    # 添加屏幕工作分辨率大小（经过缩放）以辨识在不同缩放和屏幕位置摆放下导致的问题
    backup_folder_name += f'@({screen_real_width}x{screen_real_height})'

    return backup_folder_name


def print_screen_info():
    print("------------------------")
    print("注: 这个是屏幕工作区域的分辨率（所有屏幕之和再经过缩放），并非显示器的分辨率，无需在意")
    print(f"当前工作区域分辨率: {screen_real_width} x {screen_real_height}")
    print("屏幕信息:")
    print("------------------------")
    for screen in screen_list:
        print(f"名称: {screen.name.replace('\\\\.\\', '')}")
        print(f"主屏幕: {'是' if screen.is_primary else '否'}")
        print(f"分辨率: {screen.width} x {screen.height}")
        print("------------------------")


def get_process_by_name(name):
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        if name in proc.info['name']:
            return proc
    return None


def backup_function():
    # 检查备份文件是否存在,不存在则创建
    if not os.path.exists(BACKUP_PATH):
        print(f"备份文件不存在，创建备份文件夹,路径为:{BACKUP_PATH}")
        os.mkdir(BACKUP_PATH)
        os.mkdir(backup_folder_path)
    elif not os.path.exists(backup_folder_path):
        print(f"备份文件不存在，创建备份文件夹,路径为:{backup_folder_path}")
        os.mkdir(backup_folder_path)

    for filename in DATA_NAME_LIST:
        # 复制并且覆盖文件
        shutil.copy(APP_DATA_PATH + "\\" + filename, backup_folder_path + "\\" + filename)
        print(f"复制文件:\n{APP_DATA_PATH}\\{filename} 到 {backup_folder_path}")

    # 增加副本，防止把恢复按成备份
    if input("是否需要创建防手滑副本，需要创建请按Y（不需要直接回车即可）:") == 'Y':
        back_backup_function()

def back_backup_function():
    if not os.path.exists(backup_folder_path + ".back"):
        print(f"文件不存在，创建防手滑文件夹,路径为:{backup_folder_path}")
        os.mkdir(backup_folder_path + ".back")

    for filename in DATA_NAME_LIST:
        shutil.copy(APP_DATA_PATH + "\\" + filename, backup_folder_path + ".back" + "\\" + filename)
    print(f"已创建备份副本{backup_folder_path}.back")


def restore_function():
    # 检查备份文件是否存在
    is_exist = os.path.exists(backup_folder_path)

    # 通过进程列表名找到进程
    process = get_process_by_name(PROCESS_NAME)
    if process is None:
        print("未找到进程!")
        return
    process_path = process.exe()

    # 终止进程
    print("尝试终止进程...")
    process.kill()

    # 如果备份文件路径存在,则进行恢复
    if is_exist:
        for filename in DATA_NAME_LIST:
            # 复制并且覆盖文件
            shutil.copy(backup_folder_path + "\\" + filename, APP_DATA_PATH + "\\" + filename)
            print(f"复制文件:\n{backup_folder_path}\\{filename} 到 {APP_DATA_PATH}")

    print("重启进程中...")
    try:
        subprocess.Popen(process_path, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"启动进程失败: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

    return


if __name__ == "__main__":
    init()

    if not os.path.exists(APP_DATA_PATH):
        print("没有AppData文件，请确认您已经安装了腾讯桌面管理！或者检查APP_DATA是否正确！")
        sleep(3)
        exit()


    print(datetime.datetime.today())
    print_screen_info()

    switcher = {
        "1": backup_function,
        "2": restore_function,
        "0": lambda : exit()
    }

    while True:
        print("------------------------")
        print("OPTION:")
        print("1.备份")
        print("2.恢复")
        print("0.退出")
        print("请选择:", end="")
        option = str(input())
        print("------------------------")
        print("Start ...")
        fun = switcher.get(option)
        fun()
