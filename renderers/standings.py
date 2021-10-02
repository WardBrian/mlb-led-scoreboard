try:
    from rgbmatrix import graphics
except ImportError:
    from RGBMatrixEmulator import graphics

from data.config.color import Color
from data.config.layout import Layout
from data.standings import Standings
from utils import center_text_position


def get_color_node(colors, league):
    # try the league-specific color node.  If not present, go with the standard "standings"
    color_node = f"standings_{league}"
    try:
        colors.graphics_color(f"{color_node}.divider")
    except KeyError:
        color_node = "standings"
    return color_node


def render_standings(canvas, layout: Layout, colors: Color, standings: Standings, stat):
    league = standings.preferred_divisions[standings.current_division_index].split()[0].lower()
    color_node = get_color_node(colors, league)
    __fill_bg(canvas, layout, colors, color_node)
    if canvas.width > 32:
        __render_static_wide_standings(canvas, layout, colors, standings, color_node)
    else:
        return __render_rotating_standings(canvas, layout, colors, standings, stat, color_node)


def __fill_bg(canvas, layout, colors, color_node):
    coords = layout.coords("standings")
    bg_color = colors.graphics_color(f"{color_node}.background")
    for y in range(0, coords["height"]):
        graphics.DrawLine(canvas, 0, y, coords["width"], y, bg_color)


def __render_rotating_standings(canvas, layout, colors, standings, stat, color_node):
    coords = layout.coords("standings")
    font = layout.font("standings")
    divider_color = colors.graphics_color(f"{color_node}.divider")
    stat_color = colors.graphics_color(f"{color_node}.stat")
    team_stat_color = colors.graphics_color(f"{color_node}.team.stat")
    team_name_color = colors.graphics_color(f"{color_node}.team.name")
    team_elim_color = colors.graphics_color(f"{color_node}.team.elim")
    team_clinched_color = colors.graphics_color(f"{color_node}.team.clinched")

    offset = coords["offset"]

    graphics.DrawLine(canvas, 0, 0, coords["width"], 0, divider_color)

    graphics.DrawText(canvas, font["font"], coords["stat_title"]["x"], offset, stat_color, stat.upper())
    graphics.DrawLine(canvas, coords["divider"]["x"], 0, coords["divider"]["x"], coords["height"], divider_color)

    for team in standings.current_standings().teams:
        graphics.DrawLine(canvas, 0, offset, coords["width"], offset, divider_color)

        team_text = "{:3s}".format(team.team_abbrev)
        stat_text = str(getattr(team, stat))
        color = team_elim_color if team.elim else (team_clinched_color if team.clinched else team_name_color)
        graphics.DrawText(canvas, font["font"], coords["team"]["name"]["x"], offset, color, team_text)
        color = team_elim_color if team.elim else (team_clinched_color if team.clinched else team_stat_color)
        graphics.DrawText(canvas, font["font"], coords["team"]["record"]["x"], offset, color, stat_text)

        offset += coords["offset"]


def __render_static_wide_standings(canvas, layout, colors, standings, color_node):
    coords = layout.coords("standings")
    font = layout.font("standings")
    divider_color = colors.graphics_color(f"{color_node}.divider")
    bg_color = colors.graphics_color(f"{color_node}.background")
    team_stat_color = colors.graphics_color(f"{color_node}.team.stat")
    team_name_color = colors.graphics_color(f"{color_node}.team.name")
    team_elim_color = colors.graphics_color(f"{color_node}.team.elim")
    team_clinched_color = colors.graphics_color(f"{color_node}.team.clinched")
    start = coords.get("start", 0)
    offset = coords["offset"]

    graphics.DrawLine(canvas, 0, start, coords["width"], start, divider_color)

    graphics.DrawLine(
        canvas, coords["divider"]["x"], start, coords["divider"]["x"], start + coords["height"], divider_color
    )

    offset += start

    for team in standings.current_standings().teams:
        graphics.DrawLine(canvas, 0, offset, coords["width"], offset, divider_color)

        color = team_elim_color if team.elim else (team_clinched_color if team.clinched else team_name_color)
        team_text = team.team_abbrev
        graphics.DrawText(canvas, font["font"], coords["team"]["name"]["x"], offset, color, team_text)

        record_text = "{}-{}".format(team.w, team.l)
        record_text_x = center_text_position(record_text, coords["team"]["record"]["x"], font["size"]["width"])

        if "-" in str(team.gb):
            gb_text = " -  "
        else:
            gb_text = "{:>4s}".format(str(team.gb))
        gb_text_x = coords["team"]["games_back"]["x"] - (len(gb_text) * font["size"]["width"])

        color = team_elim_color if team.elim else (team_clinched_color if team.clinched else team_stat_color)
        graphics.DrawText(canvas, font["font"], record_text_x, offset, color, record_text)
        graphics.DrawText(canvas, font["font"], gb_text_x, offset, color, gb_text)

        offset += coords["offset"]

    __fill_standings_footer(canvas, layout, divider_color, bg_color)


def __fill_standings_footer(canvas, layout, divider_color, bg_color):
    coords = layout.coords("standings")
    end = coords["height"] + coords.get("start", 0)
    graphics.DrawLine(canvas, 0, end, coords["width"], end, divider_color)
    for i in range(end + 1, canvas.height):
        graphics.DrawLine(canvas, 0, i, coords["width"], i, bg_color)
