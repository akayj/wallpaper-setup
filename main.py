# -*- coding: utf-8 -*-
import mimetypes
import os
import platform
import re
import subprocess
import sys
from typing import List, Tuple

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin


import requests
from bs4 import BeautifulSoup
from alive_progress import alive_it

WALLPAPER_HOME = os.getenv("WALLPAPER_HOME", "./wallpapers")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/112.0.0.0 Safari/537.36"
)


def _get_win_resolution_size() -> Tuple[int, int]:
    try:
        import winreg
    except ImportError:
        import _winreg as winreg

    reg_path = (
        r"SYSTEM\\ControlSet001\\Enum\\DISPLAY"
        r"\\AOC2403"  # TODO: hard code
        r"\\5&1ec8d87e&0&UID0\\Device Parameters"
    )
    info = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
    value = winreg.QueryValueEx(info, "EDID")[0]

    width = value[56] + (value[58] >> 4) * 256
    height = value[59] + (value[61] >> 4) * 256

    return width, height


def _get_mac_resolution_size() -> Tuple[int, int] or None:
    x = subprocess.run(["system_profiler", "SPDisplaysDataType"], capture_output=True)
    if x.returncode:
        return

    for line in x.stdout.splitlines():
        if b"Resolution" in line:
            line = line.strip()
            g = re.findall(rb"\d+", line)
            if len(g) != 2:
                break
            return int(g[0]), int(g[1])


def get_resolution_size() -> Tuple[int, int] or None:
    system_name = platform.system().lower()

    if system_name == "darwin":
        return _get_mac_resolution_size()
    elif system_name == "windows":
        return _get_win_resolution_size()

    return None


def resolve_image_page(url):
    headers = {
        "User-Agent": USER_AGENT,
    }
    r = requests.get(url, headers=headers)
    if not r.ok:
        return

    html = BeautifulSoup(r.content, "html.parser")

    meta = html.find("meta", attrs={"property": "og:image"})
    image_url = meta.attrs["content"]

    detail_text = html.select_one("div.details div.text")
    image_name = detail_text.find("h1").text
    image_desc = detail_text.find("h2").text

    return dict(url=image_url, name=image_name, desc=image_desc)


def download_image(url, name, save_to):
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, stream=True)
    if not r.ok:
        return

    os.makedirs(save_to, exist_ok=True)

    ext = mimetypes.guess_extension(r.headers["Content-Type"])
    save_as = os.path.join(save_to, name + ext)

    if os.path.exists(save_as):
        print(f"{name} already exist, skip...")
        return

    with open(save_as, "wb") as f:
        bar = alive_it(r.iter_content(chunk_size=1024), bar="smooth")
        for chunk in bar:
            if chunk:
                f.write(chunk)
                bar.text(f"{f.tell() / 1024.0} KB downloaded")

        print("%s downloaded(%.2f KB)" % ((name + ext), f.tell() / 1024.0))


def list_images(top=1, rh=None, rw=None) -> List[str]:
    qs = {}
    if rh and rw:
        qs.update(height=rh, width=rw)

    r = requests.get(
        "https://wallpaperhub.app/wallpapers",
        headers={"User-Agent": USER_AGENT},
        params=qs,
        timeout=5,
    )
    if not r.ok:
        print(f"fetch image list failed: {r.reason}")
        sys.exit(1)

    html = BeautifulSoup(r.content, "html.parser")

    anchors = html.select("div.wallpapersContent a")[:top]
    return [urljoin("https://wallpaperhub.app/", a["href"]) for a in anchors]


def main(count=1):
    size = get_resolution_size()
    if size is None:
        sys.stderr.write("could not resolve display resolution")
        return

    rw, rh = size
    print(f"resolved resolution, width: {rw}, height: {rh}")

    page_links = list_images(count, rh, rw)
    if len(page_links) > 0:
        print(f"{len(page_links)} images will download to {WALLPAPER_HOME}")

    for page in page_links:
        detail = resolve_image_page(page)
        name = detail["name"].replace(" ", "+").replace("?", "")
        desc = detail["desc"].replace("/", "_").replace(",", "_").replace(" ", "_")
        download_image(detail["url"], name + desc, WALLPAPER_HOME)


if __name__ == "__main__":
    main(50)
