"""A self-reported expertise galaxy: arms are areas, stars are technologies."""

import random

from generator.motion import Motion
from generator.plates import galaxy
from generator.svg import PARTICLE_GROUP, frame, num, star, star_defs
from generator.typeset import Typesetter, wrap


def render(profile, areas, theme, mobile=False, motion=True, seed=""):
    for keep in galaxy.THINNING:
        svg = _compose(profile, areas, theme, mobile, motion, seed, keep)
        if len(svg.encode()) <= galaxy.BYTE_BUDGET:
            break
    return svg


def _compose(profile, areas, theme, mobile, motion, seed, keep):
    geo = galaxy.Geometry(mobile, len(areas))
    left = 24 if mobile else 44
    room = geo.width - left * 2 if mobile else 370
    legend = []
    y = 508 if mobile else 222
    for area in areas:
        lines = wrap(', '.join(area['items']), 13.5, 'regular', room - 17, max_lines=20)
        legend.append((area, y, lines))
        y += 22 + len(lines) * 17 + (35 if mobile else 26)
    geo.height = max(960 if mobile else 610, y + 55)
    if not mobile:
        geo.cy = 286
    mo, ts = Motion(motion), Typesetter()
    rng = random.Random(f"expertise:{seed}")
    dust_defs, dust_body = galaxy.dust(geo, [geo.radius * .94] * len(areas), theme, rng, mo, keep)
    defs = [star_defs(theme), dust_defs]
    body = [galaxy._sky(geo, theme, rng, mo),
            f'<g transform="translate({geo.cx} {geo.cy})" {PARTICLE_GROUP}>'
            f'<g{mo.cls("soft", delay=.2)}>{dust_body}</g></g>']
    name_size = 32 if mobile else 38
    body.append(ts.line(left, 52 if mobile else 80, profile['name'], name_size, theme.ink, 'light'))
    body.append(ts.line(left, 80 if mobile else 112, profile['tagline'], 17, theme.mute, 'italic'))
    if not mobile:
        for index, line in enumerate(wrap(profile.get('philosophy', ''), 14, 'italic', room, max_lines=2)):
            body.append(ts.line(left, 144 + index * 19, line, 14, theme.mute, 'italic'))

    # Equal visual weights: brightness and arm lengths do not imply measured proficiency.
    positions, labels = {}, []
    for index, area in enumerate(areas):
        items = area['items']
        for q, item in enumerate(items):
            radius = geo.radius * (.25 + .62 * (q + .5) / len(items))
            positions[item] = geo.point(index, radius)
            x, y = positions[item]
            body.append(f'<g transform="translate({num(x)} {num(y)})">'
                        f'<g{mo.cls("pop", delay=.5 + index * .12 + q * .06)}>'
                        f'{star(2, "now", theme, mo, phase=index + q * .37, scale=.65)}</g></g>')
        labels.extend(area.get('anchors', items[:1]))

    obstacles = [(0, 0, geo.width, 100), (0, 480, geo.width, geo.height - 480)] if mobile else [(0, 0, 420, geo.height)]
    written = {name: ('SDD' if name.startswith('SDD (') else
                     'XP' if name == 'Extreme Programming' else name) for name in positions}
    for name, (x, y, anchor, box) in galaxy.place_labels(
            labels, positions, {name: 2 for name in positions}, geo, obstacles, written).items():
        body.append(f'<g{mo.cls("soft", delay=1.4)}>'
                    f'{ts.line(x, y, written[name], galaxy.label_size(geo), theme.ink, anchor=anchor, halo=(theme.bg, 3, .95))}</g>')

    for area, y, lines in legend:
        body.append(f'<circle cx="{left + 4}" cy="{y - 5}" r="3" fill="{theme.now}"/>')
        body.append(ts.line(left + 17, y, area['name'], 17 if mobile else 18, theme.ink, 'italic'))
        for line_index, line in enumerate(lines):
            body.append(ts.line(left + 17, y + 22 + line_index * 17, line, 13.5, theme.mute))
    footer = 'Professional focus areas · Technologies & practices'
    for index, line in enumerate(wrap(footer, 12, 'italic', geo.width - 2 * left, max_lines=2)):
        body.append(ts.line(left, geo.height - 40 + index * 16, line, 12, theme.mute, 'italic'))
    defs.append(ts.defs())
    desc = 'Self-reported professional focus. ' + '; '.join(
        area['name'] + ': ' + ', '.join(area['items']) for area in areas)
    return frame(theme, geo.width, geo.height, ''.join(body),
                 f"Professional galaxy of {profile['name']}", desc, ''.join(defs), mo)
