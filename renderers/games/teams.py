try:
    from rgbmatrix import graphics
except ImportError:
    from RGBMatrixEmulator import graphics


def render_team_banner(canvas, layout, team_colors, home_team, away_team, full_team_names, show_hits_errors):
    default_colors = team_colors.color("default")

    away_colors = __team_colors(team_colors, away_team.abbrev)
    try:
        away_team_color = away_colors["home"]
    except KeyError:
        away_team_color = team_colors.color("default.home")

    home_colors = __team_colors(team_colors, home_team.abbrev)
    try:
        home_team_color = home_colors["home"]
    except KeyError:
        home_team_color = team_colors.color("default.home")

    try:
        away_team_accent = away_colors["accent"]
    except KeyError:
        away_team_accent = team_colors.color("default.accent")

    try:
        home_team_accent = home_colors["accent"]
    except KeyError:
        home_team_accent = team_colors.color("default.accent")

    bg_coords = {}
    bg_coords["away"] = layout.coords("teams.background.away")
    bg_coords["home"] = layout.coords("teams.background.home")

    accent_coords = {}
    accent_coords["away"] = layout.coords("teams.accent.away")
    accent_coords["home"] = layout.coords("teams.accent.home")

    for team in ["away", "home"]:
        for x in range(bg_coords[team]["width"]):
            for y in range(bg_coords[team]["height"]):
                color = away_team_color if team == "away" else home_team_color
                x_offset = bg_coords[team]["x"]
                y_offset = bg_coords[team]["y"]
                canvas.SetPixel(x + x_offset, y + y_offset, color["r"], color["g"], color["b"])

    for team in ["away", "home"]:
        for x in range(accent_coords[team]["width"]):
            for y in range(accent_coords[team]["height"]):
                color = away_team_accent if team == "away" else home_team_accent
                x_offset = accent_coords[team]["x"]
                y_offset = accent_coords[team]["y"]
                canvas.SetPixel(x + x_offset, y + y_offset, color["r"], color["g"], color["b"])

    __render_team_text(canvas, layout, away_colors, away_team, "away", full_team_names, default_colors)
    __render_team_text(canvas, layout, home_colors, home_team, "home", full_team_names, default_colors)

    # these are used for alignment
    score_spacing = {
        "runs": len(str(max(away_team.runs, home_team.runs))),
        "hits": len(str(max(away_team.hits, home_team.hits))),
        "errors": len(str(max(away_team.errors, home_team.errors))),
    }
    __render_team_score(canvas, layout, away_colors, away_team, "away", default_colors, score_spacing, show_hits_errors)
    __render_team_score(canvas, layout, home_colors, home_team, "home", default_colors, score_spacing, show_hits_errors)


def __team_colors(team_colors, team_abbrev):
    try:
        team_colors = team_colors.color(team_abbrev.lower())
    except KeyError:
        team_colors = team_colors.color("default")
    return team_colors


def __render_team_text(canvas, layout, colors, team, homeaway, full_team_names, default_colors):
    text_color = colors.get("text", default_colors["text"])
    text_color_graphic = graphics.Color(text_color["r"], text_color["g"], text_color["b"])
    coords = layout.coords("teams.name.{}".format(homeaway))
    font = layout.font("teams.name.{}".format(homeaway))
    team_text = "{:3s}".format(team.abbrev.upper())
    if full_team_names and canvas.width > 32:
        team_text = "{:13s}".format(team.name)
    graphics.DrawText(canvas, font["font"], coords["x"], coords["y"], text_color_graphic, team_text)


def __render_score_component(canvas, layout, colors, homeaway, default_colors, coords, component_val, width):
    # return actual calculated x coord.
    text_color = colors.get("text", default_colors["text"])
    text_color_graphic = graphics.Color(text_color["r"], text_color["g"], text_color["b"])
    font = layout.font(f"teams.runs.{homeaway}")  # just use the runs font
    component_val = str(component_val)
    std_spacing = True
    for i in range(width):
        score_x = coords["x"] - font["size"]["width"] + 1
        coords["x"] = score_x
        if len(component_val) > i:
            c = component_val[len(component_val) - i - 1]
            graphics.DrawText(canvas, font["font"], score_x, coords["y"], text_color_graphic, c)
    return score_x - 1


def __render_team_score(canvas, layout, colors, team, homeaway, default_colors, score_spacing, show_hits_errors):
    if show_hits_errors:
        coords = layout.coords(f"teams.runs.{homeaway}").copy()
        x_calc = __render_score_component(
            canvas, layout, colors, homeaway, default_colors, coords, team.errors, score_spacing["errors"]
        )
        coords["x"] = x_calc - 2
        x_calc = __render_score_component(
            canvas, layout, colors, homeaway, default_colors, coords, team.hits, score_spacing["hits"]
        )
        coords["x"] = x_calc - 2
        x_calc = __render_score_component(
            canvas, layout, colors, homeaway, default_colors, coords, team.runs, score_spacing["runs"]
        )
    else:
        coords = layout.coords(f"teams.runs.{homeaway}").copy()
        __render_score_component(
            canvas, layout, colors, homeaway, default_colors, coords, team.runs, score_spacing["runs"]
        )
