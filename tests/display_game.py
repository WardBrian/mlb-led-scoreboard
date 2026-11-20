import sys
import re
import json
import pathlib
import logging
from collections import namedtuple

# hack: allow importing from parent directory
sys.path.append(str(pathlib.Path(__file__).parent.parent.absolute()))

from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions
from RGBMatrixEmulator.internal.emulator_config import RGBMatrixEmulatorConfig

from data.config import Config
from data.config.layout import Layout
from data.game import Game
from data.leagues import LEAGUES

from renderers.main import MainRenderer, frame_pacer

RAW_CONFIG = pathlib.Path(__file__).parent / "fixtures" / "emulator_raw_config.json"

DIMENSIONS_RE = re.compile(r"w(\d+)h(\d+)")


def get_demo_game(config):
    # Brewers @ Nationals, 2019-08-17 (MIL won 15-14 in 14 innings)
    game = Game.from_scheduled(
        {
            "league": LEAGUES["MLB"],
            "game_id": 565956,
            "game_date": "2019-08-17",
            "national_broadcasts": [],
            "series_status": "",
        },
        config,
    )
    if game is None:
        sys.exit("Could not load game data from the MLB API.")
    # at this time, Yelich hits a single and the game is live
    game.update(force=True, testing_params={"timecode": "20190817_231033"})
    config.layout.state_for_game(game)
    return game


def parse_dimensions(coords_path):
    match = DIMENSIONS_RE.match(coords_path.stem)
    if not match:
        raise ValueError(
            f"Can't determine matrix size from '{coords_path.name}'. Expected a filename starting with 'w<width>h<height>', like the ones in coordinates/examples."
        )
    return int(match.group(1)), int(match.group(2))


def load_layout(coords_path, width, height):
    with open(coords_path) as f:
        layout_json = json.load(f)
    return Layout(layout_json, width, height)


def matrix_options(width, height, raw=False):
    if raw:
        RGBMatrixEmulatorConfig.CONFIG_PATH = RAW_CONFIG
    options = RGBMatrixOptions()
    options.rows = height
    options.cols = width
    return options


if __name__ == "__main__":
    logging.getLogger("mlbled").setLevel(logging.DEBUG)

    if len(sys.argv) < 2:
        sys.exit(f"Usage: python {pathlib.Path(__file__).name} <coordinates-file.json> [save]")

    # pop our own args off before Config() parses sys.argv for its CLI flags
    coords_path = pathlib.Path(sys.argv.pop(1))

    save = sys.argv[-1] == "save"
    if save:
        sys.argv.pop()

    width, height = parse_dimensions(coords_path)

    matrix = RGBMatrix(options=matrix_options(width, height, raw=save))

    config = Config()
    config.sync_amount = 0
    config.layout = load_layout(coords_path, width, height)

    game = get_demo_game(config)
    FakeData = namedtuple("FakeData", ["config", "network_issues"])

    renderer = MainRenderer(matrix, FakeData(config, False), {})  # type: ignore
    renderer.scrolling_text_pos = 8

    if save:
        renderer._MainRenderer__draw_game(game)  # type: ignore
        renderer.canvas.display_adapter._dump_screenshot("game.jpg")
    else:
        while True:
            with frame_pacer(config.scrolling_speed):
                try:
                    # reload on every frame so coordinate edits show up live
                    renderer.data.config.layout = load_layout(coords_path, width, height)
                except Exception:
                    logging.exception("Error reloading layout")

                renderer._MainRenderer__draw_game(game)  # type: ignore
