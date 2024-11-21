#
# Copyright (C) 2024 by TheTeamVivek@Github, < https://github.com/TheTeamVivek >.
#
# This file is part of < https://github.com/TheTeamVivek/YukkiMusic > project,
# and is released under the MIT License.
# Please see < https://github.com/TheTeamVivek/YukkiMusic/blob/master/LICENSE >
#
# All rights reserved.
#
from strings import get_string
from YukkiMusic.misc import SUDOERS
from YukkiMusic.utils.database import get_lang, is_commanddelete_on, is_maintenance

from config import BANNED_USERS

def language(mystic):
    async def wrapper(event):
        try:
            language = await get_lang(event.chat_id)
            language = get_string(language)
        except:
            language = get_string("en")
        if not await is_maintenance():
            if event.sender_id not in SUDOERS:
                if event.is_private:
                    return await event.reply(language["maint_4"])
                return
        if await is_commanddelete_on(event.chat_id):
            try:
                await event.delete()
            except:
                pass
        return await mystic(event, language)

    return wrapper


def languageCB(mystic):
    async def wrapper(event):
        if event.sender_id in BANNED_USERS:
            return
        try:
            language = await get_lang(event.chat_id)
            language = get_string(language)
        except:
            language = get_string("en")
        if not await is_maintenance():
            if event.sender_id not in SUDOERS:
                if event.is_private:
                    await event.answer(
                        language["maint_4"],
                        alert=True,
                    )
                return

        return await mystic(event, language)

    return wrapper


def LanguageStart(mystic):
    async def wrapper(event):
        try:
            language = await get_lang(event.chat_id)
            language = get_string(language)
        except:
            language = get_string("en")
        return await mystic(event, language)

    return wrapper
