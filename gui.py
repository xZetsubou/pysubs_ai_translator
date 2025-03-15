from pysub import translate_file, config_load, config_save, update_client
from nicegui import app, ui, native
import asyncio
import os
import pysubs2

app_name = "PySubs OpenAI Translator"
app.native.window_args["background_color"] = "#111111"
app.native.window_args["resizable"] = False
# app.native.window_args["hidden"] = True
ui.dark_mode().enable()

with ui.row(wrap=False).style("position: absolute; right: 1.6%; top: 10px;"):
    css_chips = "height: 21px; border-radius: 4px; margin: 0; text-align: center;"
    ui.chip(
        "GitHub",
        on_click=lambda: ui.navigate.to("https://github.com/xZetsubou", new_tab=True),
        icon="source",
    ).classes("bg-black").style(css_chips)
    ui.chip(
        "Support",
        on_click=lambda: ui.navigate.to(
            "https://buymeacoffee.com/mrbanderx3", new_tab=True
        ),
        color="#7f6f05",
        icon="coffee",
    ).style(css_chips)
with ui.row().classes("w-full no-wrap").style("margin-top: 15px"):
    target_lang = ui.input("Insert target language").classes("w-full")
    target_lang.value = config_load().get("language", "")


async def pick_files() -> None:
    status: dict[str, set] = {}

    def callback_update(
        filename: str, translted_line: str, finished_line_num: int, max_lines_len: int
    ):
        line_num, line = finished_line_num, translted_line
        if mutli_files:
            status[filename].add(translted_line)
            new_state = f"{len(status[filename])}/{max_lines_len} Line"
            file_grid.run_row_method(filename, "setDataValue", "state", new_state)
        else:
            file_grid.run_row_method(int(line_num), "setDataValue", "state", line)

    file_grid.options["rowData"].clear()
    if not target_lang.value:
        return ui.notify("Insert target langauge", type="warning")
    file_types = ("Subtitles Files (*.ass;*.srt)",)
    results = await app.native.main_window.create_file_dialog(
        allow_multiple=True, file_types=file_types
    )

    ui.notify(f"[{len(results or [])}] Files has been loaded")
    if not results:
        return

    if mutli_files := len(results) > 1:
        # Update grid for multi-files.
        file_grid.options["columnDefs"][1]["headerName"] = "Filename"
        file_grid.options["columnDefs"][2]["headerName"] = "Status"
        for file in results:
            filename = os.path.basename(file)
            status[filename] = set("-")
            state = f"0/{len(pysubs2.load(file))} Line"
            file_grid.options["rowData"].append(
                {"id": filename, "name": filename, "state": state}
            )
    else:
        file_grid.options["columnDefs"][1]["headerName"] = "Original Line"
        file_grid.options["columnDefs"][2]["headerName"] = "Translated"
        file_path = results[0]
        subs_before = pysubs2.load(file_path, encoding="utf-8")
        for idx, line in enumerate(subs_before):
            file_grid.options["rowData"].append(
                {"id": idx, "name": line.text, "state": ""}
            )

    file_grid.update()
    with ui.dialog() as dialog, ui.card().classes("w-full"):
        with ui.row().classes("w-full"):
            ui.label("Each line represents a note.")
            ui.label("This affects the results!").classes("text-red")
        notes = ui.textarea(
            "Add notes if you want e.g. (This is a chinese anime called the outcast)"
        ).classes("w-full")
        ui.splitter(horizontal=True).classes("w-full").disable()
        ui.label("Would you like to start to translate the file?")
        with ui.row():
            ui.button("Yes", on_click=lambda: dialog.submit("Yes"))
            ui.button("No", on_click=lambda: dialog.submit("No"))

    resp = await dialog
    if resp == "Yes":
        config_save({"language": target_lang.value})
        tasks: list[asyncio.Task] = []
        for file in results:
            tasks.append(
                asyncio.create_task(
                    translate_file(
                        file,
                        target_lang.value,
                        notes.value.splitlines(),
                        callback_update=callback_update,
                    )
                )
            )

        translate_button.on_click(lambda: [task.cancel() for task in tasks])
        translate_button.on_click(lambda: file_grid.clear())
        translate_button.enable()
        try:
            await asyncio.gather(*tasks)
        except (Exception, TimeoutError) as exc:
            ui.notify(f"Error while translating: {exc}", type="negative")
        finally:
            translate_button.disable()


ui.splitter(horizontal=True).classes("w-full").disable()


with ui.tabs(
    on_change=lambda e: [
        t.style("color: teal") if str(e.value) in str(t) else t.style("color: white")
        for t in tabs
    ]
).classes("h-7") as tabs:
    one = ui.tab("Translate file", icon="home").classes("h-7").style("color: teal")
    two = ui.tab("Configuration", icon="settings").classes("h-7")
with ui.tab_panels(tabs, value=one).classes("w-full") as main_panels:
    with ui.tab_panel(one):
        ui.label("Select subtitles")
        with ui.row():
            ui.button("Select files", on_click=pick_files)
            translate_button = ui.button("Stop Translating")
            translate_button.on_click(
                lambda: ui.notify("Translating has been aborted!", type="info")
            )
            translate_button.disable()

        file_grid = ui.aggrid(
            {
                "defaultColDef": {"flex": 1},
                "columnDefs": [
                    {
                        "headerName": "id",
                        "field": "id",
                        "hide": True,
                    },
                    {
                        "headerName": "",
                        "field": "name",
                        "sortable": False,
                    },
                    {
                        "headerName": "",
                        "field": "state",
                        "sortable": False,
                    },
                ],
                "rowData": [],
                ":getRowId": "(params) => params.data.id",
                "rowSelection": "single",
            },
            theme="balham-dark",
        )

    with ui.tab_panel(two):
        ui.label(app_name + " - config.yml")

        _config = config_load()
        btn_cfg_model_name = ui.input(
            "Model Name", value=_config.get("model_name", "deepseek-chat")
        ).classes("w-full")
        btn_cfg_openai_url = ui.input(
            "OpenAI URL", value=_config.get("openai_url", "https://api.deepseek.com")
        ).classes("w-full")
        btn_cfg_apikey = ui.input("API Key", value=_config.get("api_key", "")).classes(
            "w-full"
        )

        btn = ui.button(
            "Save",
            on_click=lambda: config_save(
                {
                    "api_key": btn_cfg_apikey.value,
                    "openai_url": btn_cfg_openai_url.value,
                    "model_name": btn_cfg_model_name.value,
                }
            ),
        )
        btn.on_click(update_client)

# ui.run()
if __name__ == "__main__":
    ui.run(
        native=True,
        title=app_name,
        window_size=(800, 620),
        reload=False,
        show=False,
        port=native.find_open_port(),
    )
