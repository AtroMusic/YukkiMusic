#
# Copyright (C) 2024 by TheTeamVivek@Github, < https://github.com/TheTeamVivek >.
#
# This file is part of < https://github.com/TheTeamVivek/YukkiMusic > project,
# and is released under the MIT License.
# Please see < https://github.com/TheTeamVivek/YukkiMusic/blob/master/LICENSE >
#
# All rights reserved.
from config import LOG, LOG_GROUP_ID
from YukkiMusic import app
from YukkiMusic.utils.database import is_on_off


async def play_logs(event, streamtype):
    if await is_on_off(LOG):
        chat = await event.get_chat()
        sender = await event.get_sender()

        if chat.username:
            chatusername = f"@{chat.username}"
        else:
            chatusername = "Private Group"

        logger_text = f"""
**{app.mention} Play Log**

**Chat ID:** `{chat.id}`
**Chat Name:** {chat.title}
**Chat Username:** {chatusername}

**User ID:** `{sender.id}`
**Name:** {sender.first_name}
**Username:** @{sender.username}

**Query:** {event.raw_text.split(None, 1)[1]}
**Stream Type:** {streamtype}"""

        if chat.id != LOG_GROUP_ID:
            try:
                await app.send_message(
                    LOG_GROUP_ID,
                    logger_text,
                    link_preview=False,
                )
            except Exception:
                pass
        return
