# -*- coding: utf-8 -*-
import mimetypes
import os
import sys
from typing import List

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

try:
    import winreg
except ImportError:
    import _winreg as winreg

import requests
from bs4 import BeautifulSoup
from alive_progress import alive_it

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/112.0.0.0 Safari/537.36"
)


def get_resolution_size():
    # TODO: hard code
    reg_path = r"SYSTEM\\ControlSet001\\Enum\\DISPLAY\AOC2403\\5&1ec8d87e&0&UID0\\Device Parameters"
    info = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
    value = winreg.QueryValueEx(info, "EDID")[0]

    width = value[56] + (value[58] >> 4) * 256
    height = value[59] + (value[61] >> 4) * 256

    return width, height


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

    details = html.find("div", class_="details")
    detail_text = details.find("div", class_="text")
    image_name = detail_text.find("h1").text
    image_desc = detail_text.find("h2").text

    return dict(url=image_url, name=image_name, desc=image_desc)


def download_image(url, name, save_to):
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, stream=True)
    if not r.ok:
        return

    if not os.path.exists(save_to):
        os.mkdir(save_to)

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
    )
    if not r.ok:
        print(f"fetch image list failed: {r.reason}")
        sys.exit(1)

    html = BeautifulSoup(r.content, "html.parser")

    anchors = html.find("div", class_="wallpapersContent").find_all("a")[:top]
    return [urljoin("https://wallpaperhub.app/", a["href"]) for a in anchors]


def main(count=1):
    rw, rh = get_resolution_size()
    print(f"resolved resolution, width: {rw}, height: {rh}")

    page_links = list_images(count, rh, rw)

    for page in page_links:
        detail = resolve_image_page(page)
        name = detail["name"].replace(" ", "+").replace("?", "")
        desc = detail["desc"].replace("/", "_").replace(",", "_").replace(" ", "_")
        download_image(detail["url"], name + desc, "E:\\wallpapers\\")


if __name__ == "__main__":
    main(50)
