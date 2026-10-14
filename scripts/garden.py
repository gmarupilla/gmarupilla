#!/usr/bin/env python3
"""Render a dependency-free SVG garden and reconcile GitHub planting requests."""
import argparse
import copy
from datetime import date, datetime, timedelta, timezone
from html import escape
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from garden_art import draw_garden, project_cover
from garden_layout import ROWS, COLUMNS, PLOTS

ROOT = Path(__file__).resolve().parents[1]
REPO = 'gmarupilla/gmarupilla'
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
        fields = re.fullmatch(r'\s*### Plot\s+([A-F][1-8])\s+### Seed\s+(Oak|Pine|Sunflower|Tulip|Mushroom|Wheat)\s*', issue.get('body') or '')
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


def draw(state, day):
    return draw_garden(state, day, WEATHER[day.toordinal() % len(WEATHER)])


def cover(name, subtitle, kind):
    return project_cover(name, subtitle, kind)


def readme(state, day):
    image_version = hashlib.sha256(draw(state, day).encode()).hexdigest()[:12]
    lines = ['# Hey, I’m Akhil. Plant something before you leave.', '',
             'I build scientific software, work with maps and models, and follow the occasional infrastructure rabbit hole.', '',
             '[Website ↗](https://marupilla.dev) · [LinkedIn ↗](https://www.linkedin.com/in/gmarupilla) · [JOSS reviews ↗](https://joss.theoj.org/papers/reviewed_by/@gmarupilla)', '',
             f'![A shared island garden. Choose an empty plot in the table below.](assets/garden.svg?v={image_version})', '',
             '### Leave a little life here', '',
             'Choose an empty plot below. Pick a seed in the form, then submit the issue. The garden updates after your request runs.', '',
             '| | ' + ' | '.join(map(str, COLUMNS)) + ' |', '|' + '---|' * (len(COLUMNS)+1)]
    for row in ROWS:
        cells = []
        for c in COLUMNS:
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
    if output.name == 'preview':
        preview_page(state, output)


def preview_page(state, output):
    """A local design review with the same state and assets as its README."""
    page = ['''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Akhil · Tiny world</title>
<style>
body{margin:0;background:#0d1117;color:#e6edf3;font:16px/1.6 system-ui,sans-serif}
main{max-width:1000px;margin:24px auto;padding:24px}h1{font-size:30px;line-height:1.25}
h2{margin-top:32px;font-size:22px}a{color:#b0cfa9;text-decoration:none}
img{width:100%;display:block;margin:22px 0;border-radius:18px}
.notice{color:#c7b88f;border-bottom:1px solid #34433c;padding-bottom:12px;font:12px/1.5 monospace}
.muted{color:#9aa99f}table{width:100%;border-collapse:collapse;font-size:13px}
td,th{text-align:center;border:1px solid #34433c;padding:8px}.plot{color:#bbd2a9}
@media(max-width:600px){main{padding:14px}h1{font-size:24px}td,th{padding:4px;font-size:10px}}
</style><main>
<div class="notice">DESIGN PREVIEW · Example plants. The live garden starts empty. Planting is not active yet.</div>
<h1>Hey, I’m Akhil. Plant something before you leave.</h1>
<p>I build scientific software, work with maps and models, and follow the occasional infrastructure rabbit hole.</p>
<p><a href="https://marupilla.dev">Website ↗</a> · <a href="https://www.linkedin.com/in/gmarupilla">LinkedIn ↗</a> · <a href="https://joss.theoj.org/papers/reviewed_by/@gmarupilla">JOSS reviews ↗</a></p>
<img src="assets/garden.svg" alt="An example community garden">
<h2>Leave a little life here</h2><p>Choose an empty plot. Pick a seed in the form, then submit the issue.</p>
<table><tr><th></th>''']
    page.extend(f'<th>{c}</th>' for c in COLUMNS)
    page.append('</tr>')
    for row in ROWS:
        page.append(f'<tr><th>{row}</th>')
        for c in COLUMNS:
            plot=f'{row}{c}'
            plant=state['plots'].get(plot)
            label=plant['seed'] if plant else f'＋ {plot}'
            page.append(f'<td class="plot">{escape(label)}</td>')
        page.append('</tr>')
    page.append('</table><p><b>Seed shelf:</b> Oak · Pine · Sunflower · Tulip · Mushroom · Wheat</p><p class="muted">One plant per person per UTC day. Plants mature after four days and return to soil after 21 days.</p><h2>A few other things I’m growing</h2>')
    for repo,asset in [('AgroTerraFlow','agroterraflow'),('yieldcast','yieldcast'),('flashdry','flashdry')]:
        page.append(f'<a href="https://github.com/gmarupilla/{repo}"><img src="assets/{asset}.svg" alt="{escape(repo)} project cover"></a>')
    page.append('<p>Also on the workbench: <a href="https://github.com/gmarupilla/trialflow-agro">TrialFlow-Agro</a>, a reproducible workflow for agricultural field trials.</p><small class="muted">Inspired by Tim Burgan’s community chess. Original code and artwork.</small></main></html>')
    (output/'index.html').write_text(''.join(page))


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
                state['plots'][plot]={'seed':SEEDS[(i+i//len(COLUMNS))%len(SEEDS)], 'user':'demo-gardener', 'planted':str(day-timedelta(days=i%7))}
        state['gardeners']={'demo-gardener':len(state['plots'])}
        render(state,day,ROOT/'preview')
        return
    if args.command == 'update':
        process(state,open_requests(),day)
        (ROOT/'garden/state.json').write_text(json.dumps(state,indent=2)+'\n')
    render(state,day,ROOT)


if __name__ == '__main__':
    main()
