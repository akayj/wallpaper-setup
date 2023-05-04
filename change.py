# -*- coding:utf-8 -*-
import os
import ctypes
import sys
import time

WALLPAPER_HOME = "E:\\wallpapers"
SPI_SETDESKWALLPAPER = 20


def change(filepath):
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, filepath, 3)


def list_wallpapers(reverse=True):
    images = [os.path.join(WALLPAPER_HOME, f) for f in os.listdir(WALLPAPER_HOME)]
    return sorted(
        images,
        key=lambda img: os.stat(img).st_mtime,
        reverse=reverse,
    )


if __name__ == "__main__":
    try:
        for img in list_wallpapers():
            print(f"Change to {img}")
            change(img)
            time.sleep(60 * 30)
    except KeyboardInterrupt:
        sys.exit(0)
