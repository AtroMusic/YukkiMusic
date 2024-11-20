#
# Copyright (C) 2024 by TheTeamVivek@Github, < https://github.com/TheTeamVivek >.
#
# This file is part of < https://github.com/TheTeamVivek/YukkiMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TheTeamVivek/YukkiMusic/blob/master/LICENSE >
#
# All rights reserved.
#

import asyncio
import os
import time
from datetime import datetime, timedelta
from typing import Union

import aiohttp

import config
from config import lyrical

from ..utils.formatters import convert_bytes, get_readable_time, seconds_to_min

from telethon import Button, events
from telethon.tl.custom.message import Message
from telethon.tl.custom.file import File

downloader = {}


class TeleAPI:
    def __init__(self):
        self.chars_limit = 4096
        self.sleep = config.TELEGRAM_DOWNLOAD_EDIT_SLEEP

    async def send_split_text(self, event: events.NewMessage, string, chars_limit):
        n = chars_limit
        out = [(string[i : i + n]) for i in range(0, len(string), n)]
        j = 0
        for x in out:
            if j <= 2:
                j += 1
                await event.reply(x)
        return True

    async def get_link(self, event: events.NewMessage):
        chat = await event.get_chat()
        if chat.username:
            link = (
                f"https://t.me/{chat.username}/{event.message.reply_to.reply_to_msg_id}"
            )
        else:
            xf = str((event.chat_id))[4:]
            link = f"https://t.me/c/{xf}/{event.message.reply_to.reply_to_msg_id}"
        return link

    async def get_filename(
        self, file: File, audio: Union[bool, str] = None
    ):
        file_name = file.name or "Telegram audio file" if audio else "Telegram video file"
        return file_name

    async def get_duration(self, file: File) -> str:
        try:
            duration = file.duration
            dur = seconds_to_min(duration) if duration is not None else "Unknown"
        except Exception:
            dur = "Unknown"
        return dur

    async def get_filepath(self, file: File) -> str:
        file_id = file.id
        file_ext = file.ext or ""
        file_name = f"{file_id}{file_ext}"
        downloads_dir = os.path.realpath("downloads")
        file_name = os.path.join(downloads_dir, file_name)

        return file_name

    async def is_streamable_url(self, url: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        content_type = response.headers.get("Content-Type", "")
                        if (
                            "application/vnd.apple.mpegurl" in content_type
                            or "application/x-mpegURL" in content_type
                        ):
                            return True
                        if any(
                            keyword in content_type
                            for keyword in [
                                "audio",
                                "video",
                                "mp4",
                                "mpegurl",
                                "m3u8",
                                "mpeg",
                            ]
                        ):
                            return True
                        if url.endswith((".m3u8", ".index", ".mp4", ".mpeg", ".mpd")):
                            return True
        except aiohttp.ClientError:
            pass
        return False

    async def download(self, _, event, mystic, fname):
        left_time = {}
        speed_counter = {}
        if os.path.exists(fname):
            return True

        async def down_load():
            async def progress(current, total):
                if current == total:
                    return
                current_time = time.time()
                start_time = speed_counter.get(event.id)
                check_time = current_time - start_time
                upl = [Button.inline("🚦 Cancel Downloading", "stop_downloading")]
                if datetime.now() > left_time.get(event.id):
                    percentage = current * 100 / total
                    speed = current / check_time
                    eta = int((total - current) / speed)
                    downloader[event.id] = eta
                    eta = get_readable_time(eta)
                    if not eta:
                        eta = "0 sec"
                    total_size = convert_bytes(total)
                    completed_size = convert_bytes(current)
                    speed = convert_bytes(speed)
                    text = f"""
**Telegram Media Downloader**

**Total File Size:** {total_size}
**Completed:** {completed_size}
**Percentage:** {percentage:.2f}%
**Speed:** {speed}/s
**Elapsed Time:** {eta}"""
                    try:
                        await mystic.edit(
                            message=text, buttons=upl
                        )
                    except:
                        pass
                    left_time[event.id] = datetime.now() + timedelta(seconds=self.sleep)

            speed_counter[event.id] = time.time()
            left_time[event.id] = datetime.now()

            try:
                await app.download_media(
                    await event.get_reply_message(),
                    file=fname,
                    progress_callback=progress,
                )
                await mystic.edit(
                    "Successfully downloaded... Processing file now",
                )
                downloader.pop(event.id, None)
            except:
                await mystic.edit(_["tg_2"])

            if len(downloader) > 10:
                timers = [downloader[x] for x in downloader]
                try:
                    low = min(timers)
                    eta = get_readable_time(low)
                except:
                    eta = "Unknown"
                await mystic.edit(_["tg_1"].format(eta)
                )
                return False

        task = asyncio.create_task(down_load(), name=f"download_{event.chat_id}")
        lyrical[mystic.id] = task
        await task
        downloaded = downloader.get(event.id)
        if downloaded:
            downloader.pop(event.id)
            return False
        verify = lyrical.get(mystic.id)
        if not verify:
            return False
        lyrical.pop(mystic.id)
        return True
