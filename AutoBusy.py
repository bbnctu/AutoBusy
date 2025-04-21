import pyautogui
import time
import json
from datetime import datetime
import schedule
import ctypes
import logging
import atexit
import signal
import os

# 初始化日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("AutoBusy.log"),  # 輸出到檔案
        #logging.StreamHandler()  # 同時輸出到 console
    ]
)

# Load configuration from a file
def load_config():
    """
    從 'config.json' 檔案中載入設定。
    返回一個字典，包含執行間隔、開始時間、結束時間和滑鼠移動距離等設定。
    """
    with open('config.json', 'r') as file:
        return json.load(file)

# Simulate small mouse movement
def move_mouse(distance):
    """
    模擬滑鼠的微小移動，防止螢幕進入休眠或顯示為閒置狀態。
    :param distance: 滑鼠移動的距離（像素）。
    """
    pyautogui.moveRel(distance, 0, duration=0.1)  # 向右移動指定距離
    pyautogui.moveRel(-distance, 0, duration=0.1)  # 向左移動回到原位

# 防止系統進入休眠或關閉螢幕
def prevent_sleep():
    """
    使用 Windows API 防止系統進入休眠或關閉螢幕。
    """
    """

    logging.info("Calling prevent_sleep(): Preventing system sleep.")
    ctypes.windll.kernel32.SetThreadExecutionState(
        0x80000002  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )
    """


# 恢復系統的正常休眠狀態
def allow_sleep():
    """
    恢復系統的正常休眠狀態。
    """
    """
    logging.info("Calling allow_sleep(): Restoring system sleep state.")
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)  # ES_CONTINUOUS
    """


# 註冊清理函式
def register_exit_handlers():
    """
    註冊程式結束時的清理操作，確保恢復系統的正常休眠狀態。
    """
    """

    # 使用 atexit 確保程式正常結束時執行 allow_sleep
    atexit.register(allow_sleep)

    # 註冊 SIGINT 處理器
    logging.info("Registering SIGINT handler.")
    signal.signal(signal.SIGINT, handle_sigint)
    """

def handle_sigint(signum, frame):
    logging.info("SIGINT received. Exiting the program immediately.")
    allow_sleep()
    os._exit(0)  # 使用 os._exit 確保立即退出程式

from pynput.keyboard import Controller, Key

# 模擬鍵盤輸入
def simulate_keyboard():
    """
    模擬鍵盤按下和釋放 Shift 鍵。
    """
    keyboard = Controller()
    keyboard.press(Key.shift)
    keyboard.release(Key.shift)

# Check if the current time is within the active time range
def is_within_active_time(start_time, end_time):
    now = datetime.now().time()
    return start_time <= now <= end_time

# Main function to run the script
def main():
    """
    主函式，負責載入設定、排程任務並執行。
    """
    logging.info("Starting AutoBusy application.")
   
    print("Starting...")
    config = load_config()
    interval = config.get('interval', 60)  # 預設執行間隔為60秒
    start_time = datetime.strptime(config['start_time'], '%H:%M').time()  # 解析開始時間
    end_time = datetime.strptime(config['end_time'], '%H:%M').time()  # 解析結束時間
    distance = config.get('distance', 10)  # 預設滑鼠移動距離為10像素

    def job():
        """
        排程任務：檢查是否在啟動時間範圍內，如果是則執行滑鼠移動。
        """
        if is_within_active_time(start_time, end_time):
            prevent_sleep()  # 防止系統進入休眠
            move_mouse(distance)
            simulate_keyboard()  # 模擬鍵盤輸入
            #allow_sleep() 
        else:
            allow_sleep()  # 恢復系統的正常休眠狀態

    # 設定排程，每隔指定的秒數執行一次任務
    schedule.every(interval).seconds.do(job)

    prevent_sleep()
    register_exit_handlers()  # 註冊清理操作

    # 無限迴圈，持續執行排程
    try:
        logging.info("Entering the main loop. Waiting for scheduled tasks or interruptions.")
        while True:
            try:
                logging.debug("Running scheduled tasks.")
                schedule.run_pending()  # 執行所有已排程的任務
            except Exception as e:
                logging.error(f"Error while running scheduled tasks: {e}")
            time.sleep(1)  # 每隔 1 秒檢查一次排程，確保能捕捉 KeyboardInterrupt
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt caught. Exiting the program.")
        print("Program interrupted by user.")
    finally:
        logging.info("Exiting program and restoring system sleep state.")
        allow_sleep()  # 確保恢復系統的正常休眠狀態

if __name__ == "__main__":
    main()