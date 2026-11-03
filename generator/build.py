"""Render every plate in every variant.

RENDERERS is the list of plates: file stem -> function of the data snapshot,
the config, a theme, the mobile flag and the motion flag. Tests iterate over
it, so a new plate gets the whole contract battery by being listed here.
"""

from __future__ import annotations

from generator import model, professional
from generator.plates import VARIANTS, contributions, expertise, featured, galaxy, languages
from generator.themes import get_theme

RENDERERS = {
    "galaxy-header": lambda snap, config, theme, mobile, motion:
        expertise.render(config["profile"], config["professional_areas"], theme, mobile, motion, seed=snap.login)
        if config.get("professional_areas") else
        galaxy.render(model.galaxy(snap, config), config["profile"], theme, mobile, motion, seed=snap.login),
    "stats-card": lambda snap, config, theme, mobile, motion:
        professional.render(config["_professional_stats"], theme, mobile, motion)
        if config.get("_professional_stats") else
        contributions.render(model.weekly_series(snap), snap.counters, config["stats"]["metrics"], theme, mobile,
                             motion),
    "tech-stack": lambda snap, config, theme, mobile, motion:
        languages.render(
            professional.language_shares(config["_professional_stats"], config["languages"]["max_display"])
            if config.get("_professional_stats") else
            model.language_shares(snap, config["languages"]["exclude"], config["languages"]["max_display"]),
            config["galaxy_arms"], theme, mobile, motion,
            heading="Professional codebases, by bytes of code" if config.get("_professional_stats") else languages.HEADING),
    "projects-constellation": lambda snap, config, theme, mobile, motion:
        featured.render(model.featured(snap, config), theme, mobile, motion),
}


def render_all(config: dict, snap) -> dict:
    """{file name: SVG} for each plate in dark, light, mobile and mobile-light."""
    themes = config["themes"]
    files = {}
    for stem, render in RENDERERS.items():
        for suffix, mode, mobile in VARIANTS:
            theme = get_theme(themes[mode], mode, themes["overrides"])
            files[f"{stem}{suffix}.svg"] = render(snap, config, theme, mobile, config["motion"])
    return files
