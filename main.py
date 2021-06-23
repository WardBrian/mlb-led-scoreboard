import logging
import threading
import time

import debug
from data.config import Config
from data.data import Data
from renderers.main import MainRenderer
from utils import args, led_matrix_options

try:
    from rgbmatrix import RGBMatrix, __version__

    emulated = False
except ImportError:
    from RGBMatrixEmulator import RGBMatrix, version

    emulated = True


SCRIPT_NAME = "MLB LED Scoreboard"
SCRIPT_VERSION = "5.0.0-dev"


def main(args_in):
    # Check for led configuration arguments
    matrixOptions = led_matrix_options(args_in)

    # Initialize the matrix
    matrix = RGBMatrix(options=matrixOptions)

    # Read scoreboard options from config.json if it exists
    config = Config("config", matrix.width, matrix.height)
    logger = logging.getLogger("mlbled")
    if config.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    # Print some basic info on startup
    debug.info("%s - v%s (%sx%s)", SCRIPT_NAME, SCRIPT_VERSION, matrix.width, matrix.height)

    if emulated:
        debug.log("rgbmatrix not installed, falling back to emulator!")
        debug.log("Using RGBMatrixEmulator version %s", version.__version__)
    else:
        debug.log("Using rgbmatrix version %s", __version__)

    # Create a new data object to manage the MLB data
    # This will fetch initial data from MLB
    data = Data(config)

    # create render thread
    render = threading.Thread(target=__render_main, args=[matrix, data], name="render_thread", daemon=True)
    render.start()

    screen = get_screen_type(data)
    if screen == "news":
        __refresh_offday(render, data)
    elif screen == "standings":
        __refresh_standings(render, data)
    else:
        __refresh_games(render, data)


def __refresh_offday(render_thread: threading.Thread, data: Data):
    debug.log("Main has selected the offday information to refresh")
    while render_thread.is_alive():
        time.sleep(30)
        data.refresh_weather()
        data.refresh_news_ticker()


def __refresh_standings(render_thread: threading.Thread, data: Data):
    if data.standings.divisions:
        debug.log("Main has selected the standings to refresh")
        while render_thread.is_alive():
            time.sleep(30)
            data.refresh_standings()
    else:
        __refresh_offday(render_thread, data)


def __refresh_games(render_thread: threading.Thread, data: Data):
    debug.log("Main has selected the game and schedule information to refresh")

    starttime = time.time()
    promise_game = False

    while render_thread.is_alive():
        time.sleep(0.5)
        if data.config.standings_no_games:
            if not data.schedule.games_live():
                data.refresh_standings()
            # make sure a game is poulated
            elif not promise_game:
                promise_game = True
                data.advance_to_next_game()

        data.refresh_schedule()

        rotate = data.should_rotate_to_next_game()
        if data.schedule.games_live() and not rotate:
            data.refresh_game()

        endtime = time.time()
        time_delta = endtime - starttime
        rotate_rate = data.config.rotate_rate_for_status(data.current_game.status())

        if time_delta >= rotate_rate and data.scrolling_finished:
            starttime = time.time()
            if rotate:
                data.advance_to_next_game()


def __render_main(matrix, data):
    MainRenderer(matrix, data).render(get_screen_type(data))


def get_screen_type(data: Data):
    # Always the news
    if data.config.news_ticker_always_display:
        return "news"
    # Always the standings
    elif data.config.standings_always_display:
        return "standings"

    # Full MLB Offday
    elif data.schedule.is_offday():
        if data.config.standings_mlb_offday:
            return "standings"
        else:
            return "news"
    # Preferred Team Offday
    elif data.schedule.is_offday_for_preferred_team():
        if data.config.news_ticker_team_offday:
            return "news"
        elif data.config.standings_team_offday:
            return "standings"
    # Playball!
    else:
        return "games"


if __name__ == "__main__":
    try:
        main(args())
    except:
        debug.exception("Untrapped error in main!")
        raise
