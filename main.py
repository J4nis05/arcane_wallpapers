from PIL import Image, ImageTk
import ffmpeg
import cv2

import os
import random
import tkinter
import mimetypes
import uuid

#region Base Values
input_dir     = "videos"
output_dir    = "wallpapers"
export_prefix = "wallpaper"
window_width  = 1920
window_height = 1080


#region Random Frame Number
def random_number(max: int, min: int = 0):
    return random.randint(min, max)


#region Select Video from List
def select_video(video_list: list, frame_dict: dict):
    video = random.choice(video_list)
    frame = random_number(frame_dict[video])
    return video, frame


#region Is File a Video
def is_video(path: str):
    mime_type, _ = mimetypes.guess_type(path)

    if mime_type is not None and mime_type.startswith("video/"):
        return True
    return False


#region Get Files from in dir
def get_files(path: str):
    files = []
    all_items = os.listdir(path)

    for item in all_items:
        item_path = os.path.join(path, item)
        if os.path.isfile(item_path):
            files.append(item_path)

    return files


#region Get Frames from Video
def get_frame_count(file_path: str):
    metadata = ffmpeg.probe(file_path)
    video_streams = [stream for stream in metadata['streams'] if stream['codec_type'] == 'video']
    video_stream = video_streams[0]
    frame_count = video_stream.get('tags', {}).get('NUMBER_OF_FRAMES')
    return frame_count


#region Extract Frame
def get_frame(file: str, frame: int):
    capture = cv2.VideoCapture(file)
    if not capture.isOpened():
        return None
    
    capture.set(cv2.CAP_PROP_POS_FRAMES, frame)
    ret, frame = capture.read()
    capture.release()
    
    if not ret:
        return None

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(frame_rgb)
    
    return pil_image

#region Get Videos and Frames
# ================================================================

dir_path = f"{input_dir}/"
scanned_files = get_files(dir_path)
files = []
frame_dict = {}

for file in scanned_files:
    if is_video(file) == True:
        files.append(file)

for file in files:
    frames = get_frame_count(file)
    frame_dict[file] = int(frames)

# ================================================================

#region Get Wallpaper
# (Select a File & Frame and get the Extracted Frame)
def get_wallpaper():
    selected_video, selected_frame = select_video(files, frame_dict)
    extracted_frame = get_frame(selected_video, selected_frame)
    return extracted_frame

#region Resize to Fit in GUI
def resize_image(image, window_width = 1920):
    image_width, image_height = image.size

    if image_width > window_width:
        new_height = int((window_width / image_width) * image_height)
        return image.resize((window_width, new_height), Image.Resampling.LANCZOS)
    return image


# region history
wallpaper_frames = []
frame_index = 0

#region Tkinter Window
# ================================================================

window = tkinter.Tk()
window.title = "Wallpapers"
window.geometry(f"{window_width}x{window_height}")

current_frame = get_wallpaper()
wallpaper_frames.append(current_frame)
resized_frame = resize_image(current_frame, window_width)
previous_frame = resized_frame
next_frame = None
is_previous = False

#region Save Image
def button1_click():
    global current_frame
    filename = f"{output_dir}/{export_prefix}_{uuid.uuid4()}.png"
    current_frame.save(filename)
    print(f"Saved Image to {filename}")


#region Generate new Image
def button2_click():
    global current_frame, next_frame, wallpaper_frames, frame_index

    if frame_index+1 == len(wallpaper_frames):
        wallpaper_frames.append(get_wallpaper())
    
    frame_index += 1
    current_frame = wallpaper_frames[frame_index]

    resized = resize_image(current_frame, window_width)
    tk_image = ImageTk.PhotoImage(resized)
    image_label.config(image=tk_image)
    image_label.image = tk_image


#region Load Previous Image
def button3_click():
    global current_frame, previous_frame, next_frame, wallpaper_frames, frame_index

    if frame_index == 0:
        wallpaper_frames.insert(0, get_wallpaper())
    else:
        frame_index -= 1

    current_frame = wallpaper_frames[frame_index]

    resized = resize_image(current_frame, window_width)
    tk_image = ImageTk.PhotoImage(resized)
    image_label.config(image=tk_image)
    image_label.image = tk_image


#region Key Handlers
def key_handler_next_image(event):
    button2_click()


def key_handler_previous_image(event):
    button3_click()


#region Window Layout
button_frame = tkinter.Frame(window)
button_frame.pack(side=tkinter.TOP, fill=tkinter.X)
image_frame = tkinter.Frame(window)
image_frame.pack(expand=True, fill=tkinter.BOTH)

button1 = tkinter.Button(button_frame, text="Save", command=button1_click)
button2 = tkinter.Button(button_frame, text="Next", command=button2_click)
button1.pack(side=tkinter.LEFT, padx=20, pady=10)
button2.pack(side=tkinter.LEFT, padx=20, pady=10)

#region Load Image into GUI
tk_image = ImageTk.PhotoImage(resized_frame)
image_label = tkinter.Label(image_frame)
image_label.pack(expand=True)
image_label.config(image=tk_image)
image_label.image = tk_image

window.bind("<Right>", key_handler_next_image)
window.bind("<Left>", key_handler_previous_image)

window.mainloop()

# ================================================================
