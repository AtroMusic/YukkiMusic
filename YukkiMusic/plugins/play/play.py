#
# Copyright (C) 2024 by TheTeamVivek@Github, < https://github.com/TheTeamVivek >.
#
# This file is part of < https://github.com/TheTeamVivek/YukkiMusic > project,
# and is released under the MIT License.
# Please see < https://github.com/TheTeamVivek/YukkiMusic/blob/master/LICENSE >
#
# All rights reserved.
#
import random
import string

import config
from config import BANNED_USERS, lyrical
from strings import get_command
from YukkiMusic import (
    LOGGER,
    Apple,
    Resso,
    Saavn,
    SoundCloud,
    Spotify,
    Telegram,
    YouTube,
    app,
)

from YukkiMusic.utils import seconds_to_min, time_to_seconds
from YukkiMusic.utils.database import is_video_allowed
from YukkiMusic.utils.decorators.play import PlayWrapper
from YukkiMusic.utils.formatters import formats
from YukkiMusic.utils.inline.play import (
    livestream_markup,
    playlist_markup,
    slider_markup,
    track_markup,
)
from YukkiMusic.utils.inline.playlist import botplaylist_markup
from YukkiMusic.utils.logger import play_logs
from YukkiMusic.utils.stream.stream import stream

PLAY_COMMAND = get_command("PLAY_COMMAND")


@app.on_message(
    command=PLAY_COMMAND,
    is_group=True,
    from_user=BANNED_USERS,
    is_restricted=True,
)
@PlayWrapper
async def play_commnd(
    event,
    _,
    chat_id,
    video,
    channel,
    playmode,
    url,
    fplay,
):
    mystic = await event.reply(_["play_2"].format(channel) if channel else _["play_1"])
    video_telegram, audio_telegram, r_msg, plist_id, slider, plist_type, spotify = None, None, None, None, None, None, None
    sender = await event.get_sender()
    user_id = sender.id
    user_name = await app.create_mention(sender)
    if event.message.is_reply:
        r_msg = await event.get_reply_message()

        audio_telegram = (r_msg.audio or r_msg.voice) if r_msg else None
        video_telegram = (r_msg.video or r_msg.document) if r_msg else None

        file = r_msg.file
    if audio_telegram:
        if file.duration > config.TG_AUDIO_FILESIZE_LIMIT:
            return await mystic.edit(_["play_5"])
        duration_min = seconds_to_min(file.duration)
        if file.duration > config.DURATION_LIMIT:
            return await mystic.edit(
                _["play_6"].format(config.DURATION_LIMIT_MIN, duration_min)
            )
        file_path = await Telegram.get_filepath(file)
        if await Telegram.download(_, event, mystic, file_path):
            message_link = await Telegram.get_link(event)
            file_name = await Telegram.get_filename(file, audio=True)
            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": duration_min,
            }

            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    event.chat_id,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                if ex_type == "AssistantErr":
                    err = e
                else:
                    err = _["general_3"].format(ex_type)
                    LOGGER(__name__).error("An error occurred", exc_info=True)
                return await mystic.edit(str(err))
            return await mystic.delete()
        return
    elif video_telegram:
        if not await is_video_allowed(event.chat_id):
            return await mystic.edit(_["play_3"])
        if r_msg.document:
            try:
                if file.ext.lower().split(".")[1] not in formats:
                    return await mystic.edit(
                        _["play_8"].format(f"{' | '.join(formats)}")
                    )
            except:
                return await mystic.edit(_["play_8"].format(f"{' | '.join(formats)}"))
        if video_telegram.file_size > config.TG_VIDEO_FILESIZE_LIMIT:
            return await mystic.edit(_["play_9"])
        file_path = await Telegram.get_filepath(file)
        if await Telegram.download(_, event, mystic, file_path):
            message_link = await Telegram.get_link(event)
            file_name = await Telegram.get_filename(video_telegram)
            dur = await Telegram.get_duration(video_telegram)
            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur,
            }
            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    event.chat_id,
                    video=True,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                if ex_type == "AssistantErr":
                    err = e
                else:
                    LOGGER(__name__).error("An error occurred", exc_info=True)
                    err = _["general_3"].format(ex_type)
                return await mystic.edit(str(err))
            return await mystic.delete()
        return
    elif url:
        if await YouTube.exists(url):
            if "playlist" in url:
                try:
                    details = await YouTube.playlist(
                        url,
                        config.PLAYLIST_FETCH_LIMIT,
                        event.sender_id,
                    )
                except Exception:
                    return await mystic.edit(_["play_3"])
                streamtype = "playlist"
                plist_type = "yt"
                if "&" in url:
                    plist_id = (url.split("=")[1]).split("&")[0]
                else:
                    plist_id = url.split("=")[1]
                img = config.PLAYLIST_IMG_URL
                cap = _["play_10"]
            elif "https://youtu.be" in url:
                videoid = url.split("/")[-1].split("?")[0]
                details, track_id = await YouTube.track(
                    f"https://www.youtube.com/watch?v={videoid}"
                )
                streamtype = "youtube"
                img = details["thumb"]
                cap = _["play_11"].format(
                    details["title"],
                    details["duration_min"],
                )
            else:
                try:
                    details, track_id = await YouTube.track(url)
                except Exception:
                    return await mystic.edit(_["play_3"])
                streamtype = "youtube"
                img = details["thumb"]
                cap = _["play_11"].format(
                    details["title"],
                    details["duration_min"],
                )
        elif await Spotify.valid(url):
            spotify = True
            if not config.SPOTIFY_CLIENT_ID and not config.SPOTIFY_CLIENT_SECRET:
                return await mystic.edit(
                    "ᴛʜɪs ʙᴏᴛ ᴄᴀɴ'ᴛ ᴩʟᴀʏ sᴩᴏᴛɪғʏ ᴛʀᴀᴄᴋs ᴀɴᴅ ᴩʟᴀʏʟɪsᴛs, ᴩʟᴇᴀsᴇ ᴄᴏɴᴛᴀᴄᴛ ᴍʏ ᴏᴡɴᴇʀ ᴀɴᴅ ᴀsᴋ ʜɪᴍ ᴛᴏ ᴀᴅᴅ sᴩᴏᴛɪғʏ ᴩʟᴀʏᴇʀ."
                )
            if "track" in url:
                try:
                    details, track_id = await Spotify.track(url)
                except Exception:
                    return await mystic.edit(_["play_3"])
                streamtype = "youtube"
                img = details["thumb"]
                cap = _["play_11"].format(details["title"], details["duration_min"])
            elif "playlist" in url:
                try:
                    details, plist_id = await Spotify.playlist(url)
                except Exception:
                    return await mystic.edit(_["play_3"])
                streamtype = "playlist"
                plist_type = "spplay"
                img = config.SPOTIFY_PLAYLIST_IMG_URL
                cap = _["play_12"].format(sender.first_name)
            elif "album" in url:
                try:
                    details, plist_id = await Spotify.album(url)
                except Exception:
                    return await mystic.edit(_["play_3"])
                streamtype = "playlist"
                plist_type = "spalbum"
                img = config.SPOTIFY_ALBUM_IMG_URL
                cap = _["play_12"].format(sender.first_name)
            elif "artist" in url:
                try:
                    details, plist_id = await Spotify.artist(url)
                except Exception:
                    return await mystic.edit(_["play_3"])
                streamtype = "playlist"
                plist_type = "spartist"
                img = config.SPOTIFY_ARTIST_IMG_URL
                cap = _["play_12"].format(sender.first_name)
            else:
                return await mystic.edit(_["play_17"])
        elif await Apple.valid(url):
            if "album" in url:
                try:
                    details, track_id = await Apple.track(url)
                except Exception:
                    return await mystic.edit(_["play_3"])
                streamtype = "youtube"
                img = details["thumb"]
                cap = _["play_11"].format(details["title"], details["duration_min"])
            elif "playlist" in url:
                spotify = True
                try:
                    details, plist_id = await Apple.playlist(url)
                except Exception:
                    return await mystic.edit(_["play_3"])
                streamtype = "playlist"
                plist_type = "apple"
                cap = _["play_13"].format(sender.first_name)
                img = url
            else:
                return await mystic.edit(_["play_16"])
        elif await Resso.valid(url):
            try:
                details, track_id = await Resso.track(url)
            except Exception:
                return await mystic.edit(_["play_3"])
            streamtype = "youtube"
            img = details["thumb"]
            cap = _["play_11"].format(details["title"], details["duration_min"])
        elif await Saavn.valid(url):
            if "shows" in url:
                return await mystic.edit(_["saavn_1"])

            elif await Saavn.is_song(url):
                try:
                    file_path, details = await Saavn.download(url)
                except Exception as e:
                    ex_type = type(e).__name__
                    LOGGER(__name__).error("An error occurred", exc_info=True)
                    return await mystic.edit(_["play_3"])
                duration_sec = details["duration_sec"]
                streamtype = "saavn_track"

                if duration_sec > config.DURATION_LIMIT:
                    return await mystic.edit(
                        _["play_6"].format(
                            config.DURATION_LIMIT_MIN,
                            details["duration_min"],
                        )
                    )
            elif await Saavn.is_playlist(url):
                try:
                    details = await Saavn.playlist(
                        url, limit=config.PLAYLIST_FETCH_LIMIT
                    )
                    streamtype = "saavn_playlist"
                except Exception as e:
                    ex_type = type(e).__name__
                    LOGGER(__name__).error("An error occurred", exc_info=True)
                    return await mystic.edit(_["play_3"])

                if len(details) == 0:
                    return await mystic.edit(_["play_3"])
            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    event.chat_id,
                    streamtype=streamtype,
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                if ex_type == "AssistantErr":
                    err = e
                else:
                    err = _["general_3"].format(ex_type)
                    LOGGER(__name__).error("An error occurred", exc_info=True)
                return await mystic.edit(str(err))
            return await mystic.delete()

        elif await SoundCloud.valid(url):
            try:
                details, track_path = await SoundCloud.download(url)
            except Exception:
                return await mystic.edit(_["play_3"])
            duration_sec = details["duration_sec"]
            if duration_sec > config.DURATION_LIMIT:
                return await mystic.edit(
                    _["play_6"].format(
                        config.DURATION_LIMIT_MIN,
                        details["duration_min"],
                    )
                )
            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    event.chat_id,
                    streamtype="soundcloud",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                if ex_type == "AssistantErr":
                    err = e
                else:
                    LOGGER(__name__).error("An error occurred", exc_info=True)
                    err = _["general_3"].format(ex_type)
                return await mystic.edit(str(err))
            return await mystic.delete()
        else:
            if not await Telegram.is_streamable_url(url):
                return await mystic.edit(_["play_19"])

            await mystic.edit(_["str_2"])
            try:
                await stream(
                    _,
                    mystic,
                    event.sender_id,
                    url,
                    chat_id,
                    sender.first_name,
                    event.chat_id,
                    video=video,
                    streamtype="index",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                if ex_type == "AssistantErr":
                    err = e
                else:
                    LOGGER(__name__).error("An error occurred", exc_info=True)
                    err = _["general_3"].format(ex_type)
                return await mystic.edit(str(err))
            return await play_logs(event, streamtype="M3u8 or Index Link")
    else:
        if len(event.text.split()) < 2:
            buttons = botplaylist_markup(_)
            return await mystic.edit(
                _["playlist_1"],
                buttons=buttons,
            )
        slider = True
        query = event.text.split(None, 1)[1]
        if "-v" in query:
            query = query.replace("-v", "")
        try:
            details, track_id = await YouTube.track(query)
        except Exception:
            return await mystic.edit(_["play_3"])
        streamtype = "youtube"
    if str(playmode) == "Direct" and not plist_type:
        if details["duration_min"]:
            duration_sec = time_to_seconds(details["duration_min"])
            if duration_sec > config.DURATION_LIMIT:
                return await mystic.edit(
                    _["play_6"].format(
                        config.DURATION_LIMIT_MIN,
                        details["duration_min"],
                    )
                )
        else:
            buttons = livestream_markup(
                _,
                track_id,
                user_id,
                "v" if video else "a",
                "c" if channel else "g",
                "f" if fplay else "d",
            )
            return await mystic.edit(
                _["play_15"],
                buttons=buttons,
            )
        try:
            await stream(
                _,
                mystic,
                user_id,
                details,
                chat_id,
                user_name,
                event.chat_id,
                video=video,
                streamtype=streamtype,
                spotify=spotify,
                forceplay=fplay,
            )
        except Exception as e:
            ex_type = type(e).__name__
            if ex_type == "AssistantErr":
                err = e
            else:
                LOGGER(__name__).error("An error occurred", exc_info=True)

                err = _["general_3"].format(ex_type)
            return await mystic.edit(str(err))
        await mystic.delete()
        return await play_logs(event, streamtype=streamtype)
    else:
        if plist_type:
            ran_hash = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=10)
            )
            lyrical[ran_hash] = plist_id
            buttons = playlist_markup(
                _,
                ran_hash,
                event.sender_id,
                plist_type,
                "c" if channel else "g",
                "f" if fplay else "d",
            )
            await mystic.delete()
            await event.reply(
                file=img,
                message=cap,
                buttons=buttons,
            )
            return await play_logs(event, streamtype=f"Playlist : {plist_type}")
        else:
            if slider:
                buttons = slider_markup(
                    _,
                    track_id,
                    event.sender_id,
                    query,
                    0,
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )
                await mystic.delete()
                await event.reply(
                    file=details["thumb"],
                    message=_["play_11"].format(
                        details["title"].title(),
                        details["duration_min"],
                    ),
                    buttons=buttons,
                )
                return await play_logs(event, streamtype=f"Searched on Youtube")
            else:
                buttons = track_markup(
                    _,
                    track_id,
                    event.sender_id,
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )
                await mystic.delete()
                await event.reply(
                    file=img,
                    message=cap,
                    buttons=buttons,
                )
                return await play_logs(event, streamtype=f"URL Searched Inline")
