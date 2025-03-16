
<a  href="https://www.buymeacoffee.com/mrbanderx3"  target="_blank"><img  src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png"  alt="Buy Me A Coffee"  style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>


# Pysubs AI Translator


An asynchronous tool built with python to translate subtitles files that supported by "pysubs2" using AI, It focus on "speed" and "results"


## Features

- Supports many files format thanks to [pysubs2](https://pysubs2.readthedocs.io/en/latest/supported-formats.html) lib `SRT, ASS, SUB, MPL2, TMP, WebVTT, TTML and SAMI`

- Supports multi-files at once

- Supports GUI with Windows Executable File using nicegui lib


## Usage

**Installation**

```shell

git clone https://github.com/xZetsubou/pysubs_ai_translator .

python -m venv venv && source venv/Scripts/activate

pip install -r requirements.txt

```


**Usage**
Running the command for the first time would fail, but a `config.yml` file will appear open the config file and insert the `model, OpenAI URL and API KEY` -- by default this will initialize `deepseek` configuration, since this tool made and tested  on `deepseek`.

Translate file `note: if the src is directory it will translate all subtitles files inside`

```shell

py pysub.py -src "src/the outcast 05.ass" -target_lang arabic -notes "This is a chinese anime called The Outcast"

```


**GUI**

On windows I would recommended to download the executable `exe` file from [releases](https://github.com/xZetsubou/pysubs_ai_translator/releases)

otherwise manually follow the installation instructions above and run GUI module.

```shell
py gui.py
```
