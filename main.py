#region Imports
# ==============================================================================
import cv2
import ffmpeg
from PIL import Image, ImageTk

import mimetypes
import os
import random
import time
import tkinter as tk
import uuid
# ==============================================================================


#region Functions
# ==============================================================================

def get_files(path: str) -> list:
    files = []
    all_items = os.listdir(path)

    for item in all_items:
        item_path = os.path.join(path, item)
        if os.path.isfile(item_path):
            files.append(item_path)

    return files


def is_video(path: str) -> bool:
    mime_type, _ = mimetypes.guess_type(path)
    return mime_type is not None and mime_type.startswith("video/")


def select_video(frame_dict: dict) -> tuple[str, int]:
    keys = list(frame_dict.keys())
    video = random.choice(keys)
    frame = random.randint(0, frame_dict[video])
    return video, frame


def get_frame_count(file_path: str) -> int:
    metadata = ffmpeg.probe(file_path)
    streams = [ s for s in metadata['streams'] if s['codec_type'] == 'video' ]
    video_stream = streams[0]
    frame_count = video_stream.get('tags', {}).get('NUMBER_OF_FRAMES')
    return frame_count


def extract_frame(file: str, frame: int) -> Image.Image | None:
    try:
        capture = cv2.VideoCapture(file)
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame)
        success, frame = capture.read()
        
        if success:
            return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        return None
        
    finally:
        capture.release()


def resize_image(image, win_width = 1920, win_height = 1080) -> Image.Image:
    image_width, image_height = image.size

    width_scale = win_width / image_width
    height_scale = win_height / image_height
    scale_factor = min(width_scale, height_scale)
    
    new_width = int(image_width * scale_factor)
    new_height = int(image_height * scale_factor)
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def get_wallpaper() -> Image.Image | None:
    selected_video, selected_frame = select_video(frame_dict)
    extracted_frame = extract_frame(selected_video, selected_frame)
    return extracted_frame


def prev_image():
    global current_frame, wallpaper_frames, frame_index

    if frame_index == 0:
        return
    else:
        frame_index -= 1

    current_frame = wallpaper_frames[frame_index]
    resized = resize_image(current_frame, window.winfo_width(), window.winfo_height())
    tk_image = ImageTk.PhotoImage(resized)
    image_label.config(image=tk_image)
    image_label.image = tk_image


def save_image():
    global current_frame
    filename = f"{output_dir}/{export_prefix}_{uuid.uuid4()}.png"
    current_frame.save(filename)
    print(f"Saved Image to {filename}")


def next_image():
    global current_frame, wallpaper_frames, frame_index

    if frame_index+1 == len(wallpaper_frames):
        wallpaper_frames.append(get_wallpaper())
    
    frame_index += 1
    current_frame = wallpaper_frames[frame_index]

    resized = resize_image(current_frame, window.winfo_width(), window.winfo_height())
    tk_image = ImageTk.PhotoImage(resized)
    image_label.config(image=tk_image)
    image_label.image = tk_image


def key_handler_previous_image(event):
    prev_image()


def key_handler_save_image(event):
    save_image()


def key_handler_next_image(event):
    next_image()


def key_handler_quit(event):
    window.quit()

# ==============================================================================


#region Base Values
# ==============================================================================

input_dir        = "videos"
output_dir       = "wallpapers"
export_prefix    = "wallpaper"
window_width     = 1920
window_height    = 1080
btn_width        = 10
frame_index      = 0
dir_path         = os.path.join(input_dir)
scanned_files    = get_files(dir_path)
files            = [ file for file in scanned_files if is_video(file) ]
frame_dict       = { file: int(get_frame_count(file)) for file in files }
current_frame    = get_wallpaper()
resized_frame    = resize_image(current_frame, window_width, window_height)
wallpaper_frames = []
wallpaper_frames.append(current_frame)

preload_amount = 15
preload_start = time.time()

for i in range(preload_amount):
    start = time.time()
    wallpaper = get_wallpaper()
    wallpaper_frames.append(wallpaper)
    stop = time.time()
    print(f"Took {stop - start:3f} Seconds to Preaload Image {i + 1} / {preload_amount}")

preload_end = time.time()
print(f"Preloaded {preload_amount} Images in {preload_end - preload_start:3f} Seconds")

# ==============================================================================


#region Tkinter Window
# ==============================================================================

window = tk.Tk()
window.title = "Wallpapers"
window.geometry(f"{window_width}x{window_height}")


button_frame = tk.Frame(window)
button_frame.pack(side=tk.TOP, fill=tk.X)

image_frame = tk.Frame(window)
image_frame.pack(expand=True, fill=tk.BOTH)

btn_container = tk.Frame(button_frame)
btn_container.pack(expand=True)


button1 = tk.Button(btn_container, command=prev_image, width=btn_width, text="Previous")
button2 = tk.Button(btn_container, command=save_image, width=btn_width, text="Save")
button3 = tk.Button(btn_container, command=next_image, width=btn_width, text="Next")

button1.pack(side=tk.LEFT, padx=20, pady=10)
button2.pack(side=tk.LEFT, padx=20, pady=10)
button3.pack(side=tk.LEFT, padx=20, pady=10)


tk_image = ImageTk.PhotoImage(resized_frame)
image_label = tk.Label(image_frame)
image_label.pack(expand=True)
image_label.config(image=tk_image)
image_label.image = tk_image


window.bind("<Left>",   key_handler_previous_image)
window.bind("<Return>", key_handler_save_image)
window.bind("<Right>",  key_handler_next_image)
window.bind("<Escape>", key_handler_quit)


window.mainloop()

# ==============================================================================
