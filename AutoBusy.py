import pyautogui
import time
import json
from datetime import datetime
import schedule

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

# Check if the current time is within the active time range
def is_within_active_time(start_time, end_time):
    now = datetime.now().time()
    return start_time <= now <= end_time

# Main function to run the script
def main():
    """
    主函式，負責載入設定、排程任務並執行。
    """
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
            move_mouse(distance)

    # 設定排程，每隔指定的秒數執行一次任務
    schedule.every(interval).seconds.do(job)

    # 無限迴圈，持續執行排程
    while True:
        schedule.run_pending()  # 執行所有已排程的任務
        time.sleep(max(1, interval // 2))  # 每隔 interval/2 秒檢查一次排程，降低系統負擔

if __name__ == "__main__":
    main()