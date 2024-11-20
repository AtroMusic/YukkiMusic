#
# Copyright (C) 2024 by TheTeamVivek@Github, < https://github.com/TheTeamVivek >.
#
# This file is part of < https://github.com/TheTeamVivek/YukkiMusic > project,
# and is released under the MIT License.
# Please see < https://github.com/TheTeamVivek/YukkiMusic/blob/master/LICENSE >
#
# All rights reserved.
#
import asyncio
import json
import os
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import OperationFailure
from telethon import events
from telethon.errors import FloodWaitError as FloodWait

from config import MONGO_DB_URI, OWNER_ID
from YukkiMusic import app
from YukkiMusic.core.mongo import DB_NAME


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)  # Convert ObjectId to string
        if isinstance(obj, datetime):
            return obj.isoformat()  # Convert datetime to ISO 8601 format
        return super().default(obj)


async def ex_port(db, db_name):
    data = {}
    collections = await db.list_collection_names()

    for collection_name in collections:
        collection = db[collection_name]
        documents = await collection.find().to_list(length=None)
        data[collection_name] = documents

    file_path = os.path.join("cache", f"{db_name}_backup.txt")
    with open(file_path, "w") as backup_file:
        json.dump(data, backup_file, indent=4, cls=CustomJSONEncoder)

    return file_path


async def drop_db(client, db_name):
    await client.drop_database(db_name)


async def edit_or_reply(mystic, text):
    try:
        return await mystic.edit(text)
    except FloodWait as e:
        await asyncio.sleep(e.seconds)
        return await mystic.edit(text)
    except:
        return await app.send_message(mystic.chat_id, text)


@app.on(events.NewMessage(pattern="^/export$", from_users=OWNER_ID))
async def export_database(event):
    if MONGO_DB_URI is None:
        return await event.reply(
            "**Due to privacy issues, you can't Import/Export while using Yukki's Database.\n\nPlease provide your own MONGO_DB_URI to use these features.**"
        )

    mystic = await event.reply("Exporting your MongoDB database...")
    _mongo_async_ = AsyncIOMotorClient(MONGO_DB_URI)
    databases = await _mongo_async_.list_database_names()

    for db_name in databases:
        if db_name in ["local", "admin", DB_NAME]:
            continue

        db = _mongo_async_[db_name]
        mystic = await edit_or_reply(
            mystic,
            f"Found data of {db_name} database. **Uploading** and **Deleting**...",
        )

        file_path = await ex_port(db, db_name)
        try:
            await app.send_file(
                event.chat_id, file_path, caption=f"MongoDB backup data for {db_name}"
            )
        except FloodWait as e:
            await asyncio.sleep(e.seconds)
        try:
            await drop_db(_mongo_async_, db_name)
        except OperationFailure:
            mystic = await edit_or_reply(
                mystic,
                f"Deleting the database is not allowed in your MongoDB, so {db_name} cannot be deleted.",
            )
        try:
            os.remove(file_path)
        except:
            pass

    db = _mongo_async_[DB_NAME]
    mystic = await edit_or_reply(mystic, "Please wait...\nExporting bot data.")

    async def progress(current, total):
        try:
            await mystic.edit(f"Uploading... {current * 100 / total:.1f}%")
        except FloodWait as e:
            await asyncio.sleep(e.seconds)

    file_path = await ex_port(db, DB_NAME)
    try:
        await app.send_file(
            event.chat_id,
            file_path,
            caption=f"Mongo Backup of {app.mention}. Use /import to import this to a new MongoDB instance.",
            progress_callback=progress,
        )
    except FloodWait as e:
        await asyncio.sleep(e.seconds)

    await mystic.delete()


@app.on(events.NewMessage(pattern="^/import$", from_users=OWNER_ID))
async def import_database(event):
    if MONGO_DB_URI is None:
        return await event.reply(
            "**Due to privacy issues, you can't Import/Export while using Yukki's Database.\n\nPlease provide your own MONGO_DB_URI to use these features.**"
        )

    if not event.reply_to or not event.reply_to.document:
        return await event.reply("Please reply to an exported file to import it.")

    mystic = await event.reply("Downloading...")

    async def progress(current, total):
        try:
            await mystic.edit(f"Downloading... {current * 100 / total:.1f}%")
        except FloodWait as w:
            await asyncio.sleep(w.seconds)

    file_path = await event.reply_to.download_media(progress_callback=progress)

    try:
        with open(file_path, "r") as backup_file:
            data = json.load(backup_file)
    except (json.JSONDecodeError, IOError):
        return await edit_or_reply(
            mystic, "Invalid data format. Please provide a valid exported file."
        )

    if not isinstance(data, dict):
        return await edit_or_reply(
            mystic, "Invalid data format. Please provide a valid exported file."
        )

    _mongo_async_ = AsyncIOMotorClient(MONGO_DB_URI)
    db = _mongo_async_[DB_NAME]

    try:
        for collection_name, documents in data.items():
            if documents:
                mystic = await edit_or_reply(
                    mystic, f"Importing...\nCollection {collection_name}."
                )
                collection = db[collection_name]

                for document in documents:
                    await collection.replace_one(
                        {"_id": document["_id"]}, document, upsert=True
                    )

        await edit_or_reply(
            mystic, "Data successfully imported from the provided file."
        )
    except Exception as e:
        await edit_or_reply(mystic, f"Error during import: {str(e)}\nRolling back changes.")

    if os.path.exists(file_path):
        os.remove(file_path)
