#
# Copyright (C) 2024 by TheTeamVivek@Github, < https://github.com/TheTeamVivek >.
#
# This file is part of < https://github.com/TheTeamVivek/YukkiMusic > project,
# and is released under the MIT License.
# Please see < https://github.com/TheTeamVivek/YukkiMusic/blob/master/LICENSE >
#
# All rights reserved.
#

# This aeval and sh module is taken from < https://github.com/TheHamkerCat/WilliamButcherBot >
# Credit goes to TheHamkerCat.
#
import os
import re
import sys
import traceback
import asyncio
from io import StringIO
from time import time

from telethon import Button, events
from YukkiMusic import app
from YukkiMusic.misc import SUDOERS


async def aexec(code, event):
    local_vars = {}
    exec(
        "async def __aexec(event): "
        + "".join(f"\n {a}" for a in code.split("\n")),
        globals(),
        local_vars,
    )
    __aexec_func = local_vars["__aexec"]
    return await __aexec_func(event)


@app.on(events.MessageEdited(pattern=r"^/(ev|eval)", func=lambda e: e.sender_id in SUDOERS))
@app.on_message(
    command=["ev", "eval"],
    from_user=SUDOERS
)
async def executor(event):
    if len(event.message.text.split()) < 2:
        return await event.reply("<b>Give me something to execute</b>", parse_mode="html")
    cmd = event.message.text.split(" ", maxsplit=1)[1]
    t1 = time()
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    redirected_error = sys.stderr = StringIO()
    stdout, stderr, exc = None, None, None
    try:
        await aexec(cmd, event)
    except Exception:
        exc = traceback.format_exc()
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    evaluation = "\n"
    if exc:
        evaluation += exc
    elif stderr:
        evaluation += stderr
    elif stdout:
        evaluation += stdout
    else:
        evaluation += "Success"
    final_output = f"<b>RESULTS:</b>\n<pre>{evaluation}</pre>"
    if len(final_output) > 4096:
        filename = "output.txt"
        with open(filename, "w+", encoding="utf8") as out_file:
            out_file.write(str(evaluation))
        t2 = time()
        await event.reply(file=filename, message=f"<b>EVAL :</b>\n<code>{cmd[:980]}</code>\n\n<b>Results:</b> Attached Document", parse_mode="html")
        os.remove(filename)
    else:
        t2 = time()
        keyboard = [
            [Button.inline("⏳", f"runtime {round(t2 - t1, 3)} Seconds"),
            Button.inline("🗑", f"forceclose {event.sender_id}")],
        ]
        await event.reply(final_output, buttons=keyboard, parse_mode="html")


@app.on(events.CallbackQuery(data=re.compile(b"runtime")))
async def runtime_func_cq(event):
    runtime = event.data.decode("utf-8").split(" ", 1)[1]
    await event.answer(runtime, alert=True)


@app.on(events.CallbackQuery(data=re.compile(b"forceclose")))
async def forceclose_command(event):
    query_data = event.data.decode("utf-8").split(" ")[1]
    user_id = int(query_data.split("|")[0])
    if event.sender_id != user_id:
        return await event.answer("This is not for you, stay away from here", alert=True)
    await event.delete()
    await event.answer()


@app.on(events.MessageEdited(pattern=r"^/sh", func=lambda e: e.sender_id in SUDOERS))
@app.on_message(command="sh", from_user=SUDOERS)
async def shellrunner(event):
    if len(event.text.split()) < 2:
        return await event.reply("<b>Give some commands like:</b>\n/sh git pull"
        )

    text = event.text.split(None, 1)[1]
    output = ""

    async def run_command(command):
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            return stdout.decode().strip(), stderr.decode().strip()
        except Exception as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            errors = traceback.format_exception(
                etype=exc_type,
                value=exc_obj,
                tb=exc_tb,
            )
            return None, ''.join(errors)

    if "\n" in text:
        commands = text.split("\n")
        for cmd in commands:
            stdout, stderr = await run_command(cmd)
            output += f"<b>Command:</b> {cmd}\n"
            if stdout:
                output += f"<b>Output:</b>\n<pre>{stdout}</pre>\n"
            if stderr:
                output += f"<b>Error:</b>\n<pre>{stderr}</pre>\n"
    else:
        stdout, stderr = await run_command(text)
        if stdout:
            output += f"<b>Output:</b>\n<pre>{stdout}</pre>\n"
        if stderr:
            output += f"<b>Error:</b>\n<pre>{stderr}</pre>\n"

    if not output.strip():
        output = "<b>OUTPUT :</b>\n<code>None</code>"

    if len(output) > 4096:
        with open("output.txt", "w+") as file:
            file.write(output)
        await event.reply(
            file="output.txt",
            message="<code>Output</code>",
            parss_mode="html",
        )
        os.remove("output.txt")
    else:
        await event.reply(output)