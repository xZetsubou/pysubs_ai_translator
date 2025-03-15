"""
Usage exmpale: py deepseek_chat.py -src "src" -target_lang arabic -notes "This is a chinese anime called The Outcast"
"""

from openai import AsyncOpenAI
from typing import Callable
import json
import argparse
import asyncio
import os
import pysubs2
import yaml

if not os.path.exists("config.yml"):
    init_cfgs = {
        "openai_url": "https://api.deepseek.com",
        "api_key": "YOUR_API_KEY_HERE",
        "language": "arabic",
        "model": "deepseek-chat",
    }
    with open("config.yml", "w") as file:
        yaml.dump(init_cfgs, file)


def config_load():
    with open("config.yml", "r") as file:
        return yaml.safe_load(file)


def config_save(data):
    cfgs = config_load()
    # print(f"Update: {cfgs} with {data}")
    cfgs.update(data)
    with open("config.yml", "w") as file:
        return yaml.dump(cfgs, file)


def update_client():
    __config = config_load()
    client = AsyncOpenAI(api_key=__config["api_key"], base_url=__config["openai_url"])
    return client


client = update_client()


async def _translate(
    filepath, target_language, notes=[], updated_callback: Callable = None
) -> list[list]:
    """
    args:
        target_language: The language that you want to translate to it.
        notes: Addional notes to improve the results.
        updated_callback: a callback for each line sucessed.
    """
    filename = os.path.basename(filepath)
    subs = pysubs2.load(filepath)
    tasks_translation: list[asyncio.Task] = []
    translated_lines = []
    semo = asyncio.Semaphore(10)

    # For some-reason preparing AI with system role, makes doesn't follow the rules correctly!.
    def prepare_message(line, entries):
        return [
            {
                "role": "system",
                "content": (
                    f"You are an AI that translates subtitles into {target_language}.\n"
                    "You will receive a dictionary of subtitles, where only the middle entry needs to be translated.\n"
                    "Previous entries are already translated and should be used **only for context**—do not modify or include them in your response.\n"
                    f"Your response must contain **only** the translation of the middle subtitle **(line {line})**.\n"
                    "Do not return previous lines, explanations, formatting, or any extra text—just the translated subtitle."
                ),
            },
            {
                "role": "system",
                "content": (
                    "If you think additional context notes are helpful for the translation, feel free to use them, but otherwise, ignore them.\n"
                    + ("\n".join(f"- {note}" for note in notes))
                ),
            },
            {
                "role": "user",
                "content": json.dumps(entries, ensure_ascii=False),
            },
        ]

    async def make_request(line_num, subs_entries):
        async with semo:
            # print(f"Working on the line: {line_num}")
            res = await client.chat.completions.create(
                model=config_load().get("model_name", "deepseek-chat"),
                messages=prepare_message(line_num, subs_entries),
                stream=False,
                temperature=0.4,
                max_tokens=1000,
            )

            # print(f"[{line_num}] Finished line = {res.choices[0].message.content}")
            res_content = res.choices[0].message.content
            if updated_callback:
                updated_callback(filename, res_content, line_num, len(subs))
            translated_lines.append((line_num, res_content))

    subs_as_list: dict[int, str] = {idx: line.text for idx, line in enumerate(subs)}
    for num, sub in subs_as_list.items():
        context_lines = 4
        lines = dict(
            list(subs_as_list.items())[max(0, num - (context_lines - 1)) : num + 3]
        )
        # print(f"lines: {lines}")
        tasks_translation.append(asyncio.create_task(make_request(num, lines)))

    await asyncio.gather(*tasks_translation)
    return translated_lines


async def translate_file(
    filepath, target_language="arabic", notes=[], callback_update: Callable = None
):
    subs = pysubs2.load(filepath, encoding="utf-8")
    fails = []
    filename = os.path.basename(filepath)
    notes.append(
        f"The subtitle that will be provided next named: {filename} to help you"
    )
    # print(f"{filename} -> Subtitles lines is: {len(subs)}")

    if translated_lines := await _translate(
        filepath, target_language, notes, updated_callback=callback_update
    ):
        for key_sub in translated_lines:
            idx, text = key_sub
            subs[int(idx)].text = text
    else:
        fails.append(f"Failed to translate: {filename}")

    if fails:
        raise Exception(f"Some lines '{len(fails)}' has failed to translate. {fails}")

    subs.save(
        os.path.join(os.path.dirname(filepath), "translated_" + filename),
        encoding="utf-8",
    )
    return subs


async def translate_dir(src, lang, notes=[], updated_callback=None):
    tasks = []
    for path, dir, names in os.walk(os.path.abspath(src)):
        for name in names:
            try:
                filepath = os.path.join(path, name)
                sub = pysubs2.load(filepath)
                task = asyncio.create_task(
                    translate_file(
                        filepath,
                        lang,
                        notes,
                        callback_update=lambda _: updated_callback(name, len(sub)),
                    )
                )
                tasks.append(task)
            except:
                pass

    await asyncio.gather(*tasks)
    return tasks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="PySubs OpenAI Translator")
    parser.add_argument("-src", "-filename", help="filesname or dir", required=True)
    parser.add_argument(
        "-target_lang", "-lang", help="Targeted language", required=True
    )
    parser.add_argument("-notes", help="Notes split by comma")

    # print(parser.parse_args())
    args = parser.parse_args()
    notes = args.notes.split(",") if args.notes else ""
    if args.src:
        if os.path.isdir(os.path.abspath(args.src)):
            asyncio.run(translate_dir(args.src, args.target_lang or args.lang, notes))
        elif os.path.isfile(os.path.abspath(args.src)):
            asyncio.run(translate_file(args.src, args.target_lang or args.lang, notes))
