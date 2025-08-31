import sys
import tkinter as tk
from tkinter import filedialog
from ui import run_visualizer

def choose_image_file():
    root = tk.Tk()
    root.withdraw()
    root.update()
    path = filedialog.askopenfilename(
        title="Choose a map image",
        filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff"), ("All files", "*.*")]
    )
    root.destroy()
    return path if path else None

if __name__ == "__main__":
    print("Select an image, then pick START & GOAL.")
    try:
        path = choose_image_file()
        if path:
            run_visualizer(path)
        else:
            print("No image selected. Exiting.")
    except Exception as e:
        print("Unhandled error:", e)
        sys.exit(1)
