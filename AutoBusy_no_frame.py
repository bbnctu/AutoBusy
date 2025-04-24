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


def run_gui_with_autobusy():
    stop_event = threading.Event()
    autobusy_thread = threading.Thread(target=autobusy_job, args=(stop_event,), daemon=True)
    autobusy_thread.start()

    root = tk.Tk()
    root.title("Wealthy is watching you")
    root.iconbitmap("Wealthy.ico")
    root.overrideredirect(True)

    # === 你可自訂的參數 ===
    img_path = "Wealthy.png"
    close_icon_path = "close.png"
    lines = ["Wealthy is watching YOU!!!"]    # 支援多行
    text_area_ratio = 0.2                      # 文字區塊佔總高度比例
    text_vertical_shift = 0                    # 文字區塊可往上/下移（像素）
    line_spacing_ratio = 1.3                   # 行距比例

    max_img_w = 900*2   # 自訂最大顯示寬
    max_img_h = 500*2   # 自訂最大顯示高
    # =====================

    # ==== 合成圖與字 ====
    pil_img = Image.open(img_path).convert("RGBA")
    img_w, img_h = pil_img.size
    text_area_h = int(img_h * text_area_ratio)
    new_h = img_h + text_area_h
    new_img = Image.new("RGBA", (img_w, new_h), (255, 255, 255, 0))
    new_img.paste(pil_img, (0, 0))

    draw = ImageDraw.Draw(new_img)
    font_path = "arialbd.ttf"
    max_font_size = int(text_area_h * 0.7 / len(lines))
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
        if max_line_w <= img_w * 0.95 and total_h <= text_area_h * 0.95:
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
        tx = (img_w - line_w) // 2
        outline_range = 2
        for dx in range(-outline_range, outline_range + 1):
            for dy in range(-outline_range, outline_range + 1):
                if dx != 0 or dy != 0:
                    draw.text((tx + dx, curr_y + dy), line, font=font, fill="#0022aa")
        draw.text((tx, curr_y), line, font=font, fill="#0066ff")
        curr_y += int(line_h * line_spacing_ratio)

    # === 依 max_img_w, max_img_h 縮放整個圖片+字區塊 ===
    ori_w, ori_h = new_img.size
    scale = min(max_img_w / ori_w, max_img_h / ori_h, 1.0)  # 不放大原圖
    win_w, win_h = int(ori_w * scale), int(ori_h * scale)
    show_img = new_img.resize((win_w, win_h), Image.LANCZOS)

    # ==== 將視窗置中於螢幕 ====
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - win_w) // 2
    y = (screen_height - win_h) // 2
    root.geometry(f"{win_w}x{win_h}+{x}+{y}")

    # === 顯示圖+字 ===
    canvas = tk.Canvas(root, width=win_w, height=win_h, highlightthickness=0, bd=0)
    canvas.pack(fill="both", expand=True)
    tk_img = ImageTk.PhotoImage(show_img)
    canvas.create_image(0, 0, anchor="nw", image=tk_img)

    # === 加入小X關閉圖示（右上角） ===
    close_img = Image.open(close_icon_path).resize((32, 32), Image.LANCZOS)
    tk_close_img = ImageTk.PhotoImage(close_img)
    close_btn = canvas.create_image(win_w-40, 8, anchor="nw", image=tk_close_img)
    def close_app(event=None):
        stop_event.set()
        root.destroy()
    def on_canvas_click(event):
        x1, y1 = win_w-40, 8
        x2, y2 = x1+32, y1+32
        if x1 <= event.x <= x2 and y1 <= event.y <= y2:
            close_app()
    canvas.bind("<Button-1>", on_canvas_click)
    root.bind("<Escape>", lambda e: close_app())
    root.mainloop()




if __name__ == "__main__":
    run_gui_with_autobusy()
