#!/usr/bin/env python3
"""Render a dependency-free SVG garden and reconcile GitHub planting requests."""
import argparse
import copy
from datetime import date, datetime, timedelta, timezone
from html import escape
import json
import os
from pathlib import Path
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPO = 'gmarupilla/gmarupilla'
PLOTS = [f'{row}{col}' for row in 'ABCD' for col in range(1, 7)]
SEEDS = ('Oak', 'Pine', 'Sunflower', 'Tulip', 'Mushroom', 'Wheat')
WEATHER = ('Clear skies', 'Passing clouds', 'Soft rain', 'Golden light')


def today():
    return datetime.now(timezone.utc).date()


def api(path, method='GET', data=None):
    token = os.environ['GH_TOKEN']
    request = Request('https://api.github.com/repos/' + REPO + '/' + path,
                      data=json.dumps(data).encode() if data is not None else None,
                      method=method, headers={'Authorization': 'Bearer ' + token,
                      'Accept': 'application/vnd.github+json',
                      'X-GitHub-Api-Version': '2022-11-28',
                      'Content-Type': 'application/json'})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def open_requests():
    result = []
    page = 1
    while True:
        items = api(f'issues?state=open&per_page=100&page={page}&sort=created&direction=asc')
        result.extend(i for i in items if 'pull_request' not in i and i['title'] == 'garden: plant')
        if len(items) < 100:
            return sorted(result, key=lambda i: i['number'])
        page += 1


def age(plant, day):
    return max(0, (day - date.fromisoformat(plant['planted'])).days)


def compost(state, day):
    for plot, plant in list(state['plots'].items()):
        if age(plant, day) >= 21:
            del state['plots'][plot]
            state['composted'] += 1


def process(state, issues, day):
    """Persist a decision per issue so retries cannot plant twice."""
    compost(state, day)
    for issue in issues:
        key = str(issue['number'])
        if key in state['requests']:
            continue
        user = issue['user']['login']
        fields = re.fullmatch(r'\s*### Plot\s+([A-D][1-6])\s+### Seed\s+(Oak|Pine|Sunflower|Tulip|Mushroom|Wheat)\s*', issue.get('body') or '')
        result = {'user': user, 'date': str(day), 'accepted': False}
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}', user):
            result['reason'] = 'A personal GitHub account is required.'
        elif not fields:
            result['reason'] = 'Use the planting form with a valid plot and seed.'
        elif state['last_planted'].get(user.lower()) == str(day):
            result['reason'] = 'One plant per person per UTC day. Come back tomorrow.'
        elif fields[1] in state['plots']:
            result['reason'] = 'That plot is occupied. Choose another empty plot.'
        else:
            plot, seed = fields.groups()
            state['plots'][plot] = {'seed': seed, 'user': user, 'planted': str(day)}
            state['last_planted'][user.lower()] = str(day)
            state['gardeners'][user] = state['gardeners'].get(user, 0) + 1
            result.update(accepted=True, plot=plot, seed=seed, reason=f'{seed} planted in {plot}.')
        state['requests'][key] = result


def plant_svg(seed, x, y, days):
    if days == 0:
        return f'<g transform="translate({x},{y})"><path d="M0 0v-14" stroke="#b9d89b" stroke-width="3"/><ellipse cx="-5" cy="-13" rx="7" ry="3" fill="#b9d89b" transform="rotate(25 -5 -13)"/><ellipse cx="5" cy="-18" rx="7" ry="3" fill="#8fbb7a" transform="rotate(-25 5 -18)"/></g>'
    scale = .6 if days < 4 else 1
    shapes = {
        'Oak': '<path d="M0 0v-40" stroke="#b68a60" stroke-width="7"/><circle cx="-12" cy="-41" r="17" fill="#548866"/><circle cx="14" cy="-42" r="18" fill="#709f72"/><circle cy="-59" r="18" fill="#94b985"/><path d="M0-17l12-16" stroke="#b68a60" stroke-width="4"/>',
        'Pine': '<path d="M0 0v-50" stroke="#b68a60" stroke-width="6"/><path d="M0-76l-16 29h9l-17 27h48L7-47h9Z" fill="#77a68c"/><path d="M0-76v56h24L7-47h9Z" fill="#4c7c6b"/>',
        'Sunflower': '<path d="M0 0v-48m0 27l-14-8m14 15l14-8" stroke="#8faf6d" stroke-width="4"/>' + ''.join(f'<ellipse cx="0" cy="-63" rx="6" ry="10" fill="#f0bd60" transform="rotate({a} 0 -48)"/>' for a in range(0,360,45)) + '<circle cy="-48" r="10" fill="#76543d"/>',
        'Tulip': '<path d="M0 0v-36M0-9Q-18-30-15-13M0-8Q17-29 14-12" fill="#87a976" stroke="#87a976" stroke-width="3"/><path d="M-14-48l8 6 6-10 6 10 8-6v13Q0-18-14-35Z" fill="#e79e9c"/>',
        'Mushroom': '<path d="M-5 0l2-27h8l5 27Z" fill="#e8d4b3"/><path d="M-23-24Q0-66 23-24Z" fill="#d58768"/><circle cx="-8" cy="-31" r="3" fill="#f2dfc1"/><circle cx="5" cy="-37" r="4" fill="#f2dfc1"/><circle cx="12" cy="-28" r="2" fill="#f2dfc1"/>',
        'Wheat': ''.join(f'<g transform="translate({i*10},0) rotate({i*12})"><path d="M0 0v-51" stroke="#d3b16f" stroke-width="2"/>' + ''.join(f'<ellipse cx="-4" cy="{-25-j*8}" rx="3" ry="6" fill="#edcc88" transform="rotate(-35 -4 {-25-j*8})"/><ellipse cx="4" cy="{-29-j*8}" rx="3" ry="6" fill="#d3b16f" transform="rotate(35 4 {-29-j*8})"/>' for j in range(3)) + '</g>' for i in (-1,0,1)),
    }
    return f'<g transform="translate({x},{y}) scale({scale})">{shapes[seed]}</g>'


def draw(state, day):
    weather = WEATHER[day.toordinal() % len(WEATHER)]
    n = len(state['plots'])
    svg = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="660" viewBox="0 0 1000 660" role="img" aria-labelledby="title desc">
<title id="title">Akhil's tiny world — {n} planted plots</title>
<desc id="desc">A floating garden with 24 labelled plots. Use the planting links below the image. Garden weather: {weather}.</desc>
<defs><linearGradient id="sky" x2="0" y2="1"><stop stop-color="#13282d"/><stop offset="1" stop-color="#203c3d"/></linearGradient><radialGradient id="glow"><stop stop-color="#edbb73" stop-opacity=".18"/><stop offset="1" stop-color="#edbb73" stop-opacity="0"/></radialGradient></defs>
<rect width="1000" height="660" rx="24" fill="url(#sky)"/>
<circle cx="780" cy="170" r="190" fill="url(#glow)"/>
<g fill="#9baea2" opacity=".6"><circle cx="83" cy="204" r="2"/><circle cx="890" cy="275" r="2"/><circle cx="703" cy="92" r="1.5"/><circle cx="109" cy="425" r="1.5"/><circle cx="926" cy="459" r="1.5"/></g>
<text x="52" y="49" fill="#b9c7b5" font-family="monospace" font-size="12" letter-spacing="3">A SMALL EXPERIMENT IN GROWING THINGS</text>
<text x="49" y="105" fill="#f2e9d6" font-family="Georgia,serif" font-size="48">A tiny world. Made together.</text>
<text x="52" y="139" fill="#bacabe" font-family="sans-serif" font-size="15">Leave a seed. Come back to see what grows.</text>
<circle cx="878" cy="94" r="22" fill="#ebc78f"/>
<ellipse cx="511" cy="558" rx="290" ry="32" fill="#0c2026" opacity=".5"/>
<path d="M147 432Q128 494 286 538L495 568 753 526Q877 489 850 420L711 257 293 268Z" fill="#695a48"/>
<path d="M147 432Q161 491 306 522L495 550 749 510Q826 479 850 420L711 257 293 268Z" fill="#867353"/>
<path d="M191 284Q345 197 583 223L779 292Q877 366 853 431Q776 511 525 526L305 491Q112 452 143 369Z" fill="#82966b"/>
<path d="M193 289Q345 210 583 232L779 301Q862 366 844 423Q774 498 525 515L307 480Q128 443 153 371Z" fill="#9da67b"/>
<path d="M707 438q40-29 78-8q24 18-14 35q-55 17-64-27" fill="#598b8f"/><path d="M723 442q21-13 45-3" fill="none" stroke="#a2c1b8" stroke-width="2"/>
<g fill="#d6c9a0"><ellipse cx="180" cy="389" rx="10" ry="6"/><ellipse cx="202" cy="402" rx="8" ry="5"/><ellipse cx="223" cy="413" rx="6" ry="4"/></g>''']
    for r, row in enumerate('ABCD'):
        for c in range(6):
            plot = f'{row}{c+1}'
            x, y = 280+c*79+(r%2)*12, 303+r*53
            plant = state['plots'].get(plot)
            label = f'{plot}: {plant["seed"]}, caretaker {plant["user"]}' if plant else f'{plot}: empty'
            svg.append(f'<g><title>{escape(label)}</title><ellipse cx="{x}" cy="{y}" rx="28" ry="12" fill="#677953"/><ellipse cx="{x}" cy="{y-2}" rx="26" ry="10" fill="#756448"/>')
            if plant:
                svg.append(plant_svg(plant['seed'],x,y-4,age(plant,day)))
            else:
                svg.append(f'<path d="M{x-5} {y-3}h10m-5-4v8" stroke="#c7b48b" stroke-width="1.5" opacity=".7"/>')
            svg.append(f'<text x="{x}" y="{y+23}" fill="#293e30" text-anchor="middle" font-family="monospace" font-size="10">{plot}</text></g>')
    if weather == 'Soft rain':
        svg.append('<g stroke="#9abfc0" opacity=".3">'+''.join(f'<path d="M{x} {y}l-3 9"/>' for x,y in ((191,240),(830,231),(755,182),(136,310),(870,352),(684,198),(371,187)))+'</g>')
    svg.append(f'<path d="M52 586h896" stroke="#526862"/><text x="52" y="618" fill="#e5dbc5" font-family="monospace" font-size="13">{n:02d} / 24 PLOTS · {len(state["gardeners"]):02d} GARDENERS</text><text x="948" y="618" text-anchor="end" fill="#b9c7b5" font-family="monospace" font-size="12">{weather.upper()} · {day}</text></svg>')
    return '\n'.join(svg)


def cover(name, subtitle, kind):
    marks = []
    if kind == 'terrain':
        for i in range(12):
            marks.append(f'<ellipse cx="710" cy="100" rx="{45+i*19}" ry="{20+i*11}" transform="rotate(-20 710 100)" fill="none" stroke="#98b894" stroke-width="1.4" opacity=".6"/>')
    elif kind == 'yield':
        for i,v in enumerate([32,55,46,80,64,99,120,110,142]):
            marks.append(f'<rect x="{595+i*30}" y="{190-v}" width="16" height="{v}" rx="3" fill="#e4b96f" opacity="{.3+i*.07}"/>')
    else:
        for r in range(5):
            for c in range(9):
                color=['#42695e','#6b8c6c','#a7a273','#cb9c6f','#d18b63'][min(4,(c+r)//3)]
                marks.append(f'<rect x="{595+c*29}" y="{32+r*32}" width="25" height="28" rx="3" fill="{color}"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="220" viewBox="0 0 1000 220" role="img"><title>{escape(name)} — {escape(subtitle)}</title><rect width="1000" height="220" rx="18" fill="#192f32"/><g>{"".join(marks)}</g><rect x="0" width="560" height="220" rx="18" fill="#192f32"/><text x="36" y="48" fill="#c5ab7b" font-family="monospace" font-size="11" letter-spacing="3">FROM MY WORKBENCH ↗</text><text x="33" y="105" fill="#f2e9d6" font-family="Georgia,serif" font-size="38">{escape(name)}</text><text x="36" y="147" fill="#bacabe" font-family="sans-serif" font-size="15">{escape(subtitle)}</text><text x="36" y="189" fill="#bacabe" font-family="monospace" font-size="11">{ "ILLUSTRATED PROJECT COVER" }</text></svg>'


def readme(state, day):
    lines = ['# Hey, I’m Akhil. Plant something before you leave.', '',
             'I build scientific software, work with maps and models, and follow the occasional infrastructure rabbit hole.', '',
             '[Website ↗](https://marupilla.dev) · [LinkedIn ↗](https://www.linkedin.com/in/gmarupilla) · [JOSS reviews ↗](https://joss.theoj.org/papers/reviewed_by/@gmarupilla)', '',
             '![A shared island garden. Choose an empty plot in the table below.](assets/garden.svg)', '',
             '### Leave a little life here', '',
             'Choose an empty plot below. Pick a seed in the form, then submit the issue. The garden updates after your request runs.', '',
             '| | 1 | 2 | 3 | 4 | 5 | 6 |', '|---|---|---|---|---|---|---|']
    for row in 'ABCD':
        cells = []
        for c in range(1,7):
            plot=f'{row}{c}'
            plant=state['plots'].get(plot)
            if plant:
                cells.append(f'{plant["seed"]}')
            else:
                url='https://github.com/'+REPO+'/issues/new?'+urlencode({'template':'plant.yml','plot':plot})
                cells.append(f'[＋ {plot}]({url})')
        lines.append('| **'+row+'** | '+' | '.join(cells)+' |')
    lines += ['', '**Seed shelf:** Oak · Pine · Sunflower · Tulip · Mushroom · Wheat', '',
              'One plant per person per UTC day. Sprouts grow after one day and mature after four. After 21 days, they return to soil.', '',
              'The garden refreshes daily and after planting requests. Weather is part of this imaginary world.', '', '<details>', '<summary>Meet the gardeners & recent planting requests</summary>', '']
    if state['plots']:
        lines += ['| Plot | Plant | Caretaker | Planted (UTC) |','|---|---|---|---|']
        for plot in PLOTS:
            if plot in state['plots']:
                p=state['plots'][plot]
                lines.append(f'| {plot} | {p["seed"]} | @{p["user"]} | {p["planted"]} |')
    else:
        lines.append('The first plot is waiting for its caretaker.')
    lines += ['', '**Recent requests**', '']
    for number in sorted(state['requests'],key=int,reverse=True)[:5]:
        result=state['requests'][number]
        lines.append(f'- [#{number}](https://github.com/{REPO}/issues/{number}): {result["reason"]}')
    lines += ['', '</details>', '', '### A few other things I’m growing', '']
    for repo, asset, name in [('AgroTerraFlow','agroterraflow','AgroTerraFlow'),('yieldcast','yieldcast','YieldCast'),('flashdry','flashdry','FlashDry')]:
        lines += [f'[![{name} — open the project](assets/{asset}.svg)](https://github.com/gmarupilla/{repo})', '']
    lines += ['Also on the workbench: [TrialFlow-Agro](https://github.com/gmarupilla/trialflow-agro), a reproducible workflow for agricultural field trials.', '',
              '[![JOSS Reviews](https://joss.theoj.org/badges/reviewed_by/@gmarupilla)](https://joss.theoj.org/papers/reviewed_by/@gmarupilla)', '',
              '<sub>Inspired by [Tim Burgan’s community chess](https://github.com/timburgan/timburgan). This garden uses original code and artwork.</sub>', '']
    return '\n'.join(lines)


def render(state, day, output):
    assets=output/'assets'
    assets.mkdir(parents=True,exist_ok=True)
    (assets/'garden.svg').write_text(draw(state,day))
    for filename,name,subtitle,kind in [
        ('agroterraflow','AgroTerraFlow','Agricultural suitability, with uncertainty included.','terrain'),
        ('yieldcast','YieldCast','How we test a forecast changes what we learn.','yield'),
        ('flashdry','FlashDry','Exploring flash drought through satellites and weather.','dry')]:
        (assets/(filename+'.svg')).write_text(cover(name,subtitle,kind))
    (output/'README.md').write_text(readme(state,day))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['render','preview','update','close'])
    args=parser.parse_args()
    day=today()
    state=json.loads((ROOT/'garden/state.json').read_text())
    if args.command == 'close':
        for issue in open_requests():
            result=state['requests'].get(str(issue['number']))
            if result:
                api(f'issues/{issue["number"]}',method='PATCH',data={'state':'closed','state_reason':'completed' if result['accepted'] else 'not_planned'})
        return
    if args.command == 'preview':
        state=copy.deepcopy(state)
        for i,plot in enumerate(PLOTS):
            if i%4 != 1:
                state['plots'][plot]={'seed':SEEDS[(i+i//6)%6], 'user':'demo-gardener', 'planted':str(day-timedelta(days=i%7))}
        state['gardeners']={'demo-gardener':len(state['plots'])}
        render(state,day,ROOT/'preview')
        return
    if args.command == 'update':
        process(state,open_requests(),day)
        (ROOT/'garden/state.json').write_text(json.dumps(state,indent=2)+'\n')
    render(state,day,ROOT)


if __name__ == '__main__':
    main()
