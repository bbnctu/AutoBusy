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
import threading

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont

from pynput.keyboard import Controller, Key

# ========== AutoBusy 功能區 ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("AutoBusy.log"),
    ]
)

def load_config():
    with open('config.json', 'r') as file:
        return json.load(file)

def move_mouse(distance):
    pyautogui.moveRel(distance, 0, duration=0.1)
    pyautogui.moveRel(-distance, 0, duration=0.1)

def prevent_sleep():
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(
            0x80000002  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        )
    except Exception as e:
        pass

def allow_sleep():
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)  # ES_CONTINUOUS
    except Exception as e:
        pass

def handle_sigint(signum, frame):
    logging.info("SIGINT received. Exiting the program immediately.")
    allow_sleep()
    os._exit(0)

def simulate_keyboard():
    keyboard = Controller()
    keyboard.press(Key.ctrl)
    keyboard.release(Key.ctrl)

def is_within_active_time(start_time, end_time):
    now = datetime.now().time()
    return start_time <= now <= end_time

def autobusy_job(stop_event):
    config = load_config()
    interval = config.get('interval', 60)
    start_time = datetime.strptime(config['start_time'], '%H:%M').time()
    end_time = datetime.strptime(config['end_time'], '%H:%M').time()
    distance = config.get('distance', 10)

    def job():
        if is_within_active_time(start_time, end_time):
            prevent_sleep()
            move_mouse(distance)
            simulate_keyboard()
        else:
            allow_sleep()

    schedule.every(interval).seconds.do(job)
    prevent_sleep()

    while not stop_event.is_set():
        try:
            schedule.run_pending()
        except Exception as e:
            logging.error(f"Error while running scheduled tasks: {e}")
        time.sleep(1)

    allow_sleep()

# ========== Tkinter GUI ==========

import sys, os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import threading

def resource_path(relative_path):
    """
    取得正確的資源檔路徑（支援py與pyinstaller打包的exe）
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 的臨時展開目錄
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def run_gui_with_autobusy():
    stop_event = threading.Event()
    autobusy_thread = threading.Thread(target=autobusy_job, args=(stop_event,), daemon=True)
    autobusy_thread.start()

    # === 參數區 ===
    img_path = resource_path("WealthyWide2.png")
    font_path = resource_path("arialbd.ttf")
    ico_path = resource_path("Wealthy.ico")
    lines = ["Wealthy is watching YOU!!!"]
    img_area_ratio = 0.9           # 圖片在合成圖的高度比例，0.7~0.85，調大耳朵空間會多
    text_vertical_shift = 180       # 字體區域手動往上(+)下(-)移動 px
    line_spacing_ratio = 1.0        # 行距倍率
    crop_y_offset_ratio = -0.14     # 中心裁切偏移，0.0=正中，負數↑（多留上方），正數↓
    # =================

    root = tk.Tk()
    root.state('zoomed')
    root.title("Wealthy with you")
    root.iconbitmap(ico_path)
    root.attributes('-alpha', 1.0)
    root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # 載入原圖＋合成文字區
    pil_img = Image.open(img_path).convert("RGBA")
    img_w, img_h = pil_img.size
    new_h = int(img_h / img_area_ratio)
    new_w = img_w
    new_img = Image.new("RGBA", (new_w, new_h), (255,255,255,0))
    new_img.paste(pil_img, (0, 0))

    # 文字疊加
    draw = ImageDraw.Draw(new_img)
    text_area_h = new_h - img_h
    max_font_size = int(text_area_h * 6 / len(lines))
    def get_font(size):
        try:
            return ImageFont.truetype(font_path, size=size)
        except:
            return ImageFont.load_default()
    font_size = max_font_size
    while font_size > 10:
        font = get_font(font_size)
        line_heights = [draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] for line in lines]
        total_h = int(sum(line_heights) + (len(lines) - 1) * line_heights[0] * (line_spacing_ratio - 1))
        line_widths = [draw.textbbox((0, 0), line, font=font)[2] for line in lines]
        max_line_w = max(line_widths)
        if max_line_w <= new_w * 0.95 and total_h <= text_area_h * 0.95:
            break
        font_size -= 1
    line_heights = [draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] for line in lines]
    total_text_h = int(sum(line_heights) + (len(lines) - 1) * line_heights[0] * (line_spacing_ratio - 1))
    start_y = img_h + (text_area_h - total_text_h) // 2 - text_vertical_shift
    curr_y = start_y
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]
        tx = (new_w - line_w) // 2
        outline_range = 2
        for dx in range(-outline_range, outline_range + 1):
            for dy in range(-outline_range, outline_range + 1):
                if dx != 0 or dy != 0:
                    draw.text((tx + dx, curr_y + dy), line, font=font, fill="#0022aa")
        draw.text((tx, curr_y), line, font=font, fill="#0066ff")
        curr_y += int(line_h * line_spacing_ratio)

    # === 自動裁切&縮放 ===
    scale_w = screen_width / new_w
    scale_h = screen_height / new_h
    scale = max(scale_w, scale_h)

    crop_w = int(screen_width / scale)
    crop_h = int(screen_height / scale)
    # ↓↓↓ 偏移量讓你微調裁切區塊
    max_top = new_h - crop_h
    crop_top = int((max_top // 2) + crop_y_offset_ratio * max_top)
    crop_top = max(0, min(crop_top, new_h-crop_h))
    crop_bottom = crop_top + crop_h
    left = max((new_w - crop_w) // 2, 0)
    right = left + crop_w

    cropped_img = new_img.crop((left, crop_top, right, crop_bottom))
    final_img = cropped_img.resize((screen_width, screen_height), Image.LANCZOS)

    # 顯示於視窗
    canvas = tk.Canvas(root, width=screen_width, height=screen_height, highlightthickness=0, bd=0)
    canvas.pack(fill="both", expand=True)
    tk_img = ImageTk.PhotoImage(final_img)
    canvas.create_image(0, 0, anchor="nw", image=tk_img)

    # 關閉按鈕（右下角）
    def on_close():
        if messagebox.askokcancel("Wealthy love you!", "Are you sure to close Wealthy？"):
            stop_event.set()
            root.destroy()
    btn = tk.Button(root, text="Close", command=on_close, font=("Arial", 14), bg="#dddddd")
    btn_window = canvas.create_window(screen_width-180, screen_height-60, anchor="nw", window=btn)
    root.bind("<Escape>", lambda e: on_close())
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()






if __name__ == "__main__":
    run_gui_with_autobusy()
