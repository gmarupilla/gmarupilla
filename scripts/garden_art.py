"""Original pixel artwork for the garden. SVG stays portable and self-contained."""
from datetime import date
from html import escape
import random


PALETTE = {
    'd': '#24483e', 'g': '#427453', 'm': '#659659', 'l': '#9bc56c',
    'h': '#d5de8c', 't': '#765440', 'b': '#aa7750', 's': '#dda66f',
    'y': '#eab34f', 'Y': '#ffe29b', 'o': '#c77c3b', 'p': '#df8794',
    'P': '#f9b5af', 'r': '#a95767', 'w': '#fff0ce', 'c': '#d06d4f',
    'C': '#eea070', 'q': '#548f81', 'Q': '#83bda0',
}

SPRITES = {
    'sprout': [
        '.......ll', '......lhl', '.mm...ll.', 'mlmm..g..', '.mmm..g..',
        '...g.g...', '....g....', '....g....',
    ],
    'Oak': [
        '.......llll......', '.....llhhllmm....', '...llhhllllmmm...',
        '..llhlllllmmmmm..', '.lllllmmllllmmmd.', '.lllmmmlllllmmmd.',
        'llhlllllllmmmmmdd', 'lhllllllmmmmmgmdd', 'lllllmmmmmmmgmddd',
        '.mmmmmmmgmmmgddd.', '..gmmmgmmmmgddd..', '...gggttbggddd...',
        '......ttbgg......', '.....bttb........', '.....tbtb........',
        '......ttb........', '......ttb........', '.....ttbbt.......',
    ],
    'Pine': [
        '.......Q.......', '......QQq......', '......Qqq......',
        '.....QQqqd.....', '....QQqqqqd....', '.....Qqqqd.....',
        '....QQqqqqd....', '...QQQqqqqdd...', '....Qqqqqdd....',
        '...QQQqqqqdd...', '..QQQqqqqqddd..', '...QQqqqqddd...',
        '..QQQqqqqqddd..', '.QQQqqqqqqdddd.', '...qqqqqdddd...',
        '......tb.......', '......tb.......', '.....ttbb......',
    ],
    'Sunflower': [
        '.....YY.YY.....', '....YYYYYYY....', '...YYooobYYY...',
        '..YYootttbYY...', '...YottttbYYY..', '..YYootttbYY...',
        '...YYooobYY....', '....YYYYYYY....', '.....YYgYY.....',
        '.......g.......', '..ll...g.......', '..lmm..g...ll..',
        '...lmm.g..llm..', '.....mgg.llm...', '.......ggm.....',
        '.......g.......', '.......g.......',
    ],
    'Tulip': [
        '..P...P...P..', '..PP.PPP.PP..', '..PPPPPPPPP..',
        '...PPppppr...', '...Ppppprr...', '....ppprr....',
        '.....ggg.....', '......g......', '..l...g......',
        '..lm..g..l...', '...lm.g.ll...', '....lmgmm....',
        '.....ggm.....', '......g......', '......g......',
    ],
    'Mushroom': [
        '......CCC......', '....CCCCccc....', '...CCwwCcccc...',
        '..CCCwwCccwwc..', '.CwwCCCCccwwcc.', '.CwwCCCCCccccc.',
        'CCCCCCCCccccccc', '..sssssssssss..', '.....wssw......',
        '.....wssw......', '.....wssw......', '....wwssww.....',
    ],
    'Wheat': [
        '..Y.....Y......', '..Y....YY...Y..', '.YY.Y.YYo..YY..',
        '.YYoY.YYo.YYo..', '..YoY..Yo.YYo..', '..YYo..o..Yo...',
        '...Yo..o..o....', '...Yo..o..o....', '....o..o.o.....',
        '..g.o..o.o.....', '...g.o.oo......', '....go.oo......',
        '.....ooo.......', '......oo.......',
    ],
}


def rect(x, y, w, h, color, extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" {extra}/>'


def poly(points, color, extra=''):
    return f'<polygon points="{" ".join(f"{x},{y}" for x,y in points)}" fill="{color}" {extra}/>'


def text(x, y, value, size=9, color='#b3c7ba', extra=''):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-family="ui-monospace,Menlo,Consolas,monospace" {extra}>{escape(str(value))}</text>'


def sprite(seed, x, y, scale=2):
    pattern = SPRITES[seed]
    width = max(map(len, pattern))
    parts = [f'<g transform="translate({x-width*scale/2:g},{y-len(pattern)*scale:g})" shape-rendering="crispEdges">']
    for row, line in enumerate(pattern):
        for col, key in enumerate(line):
            if key in PALETTE:
                parts.append(rect(col*scale,row*scale,scale,scale,PALETTE[key]))
    return ''.join(parts) + '</g>'


def diamond(x, y, width, height, color):
    return poly([(x,y-height),(x+width,y),(x,y+height),(x-width,y)],color)


def lantern(x, y):
    return (f'<circle cx="{x}" cy="{y-9}" r="17" fill="url(#lamp)"/>'
            + rect(x-1,y-7,2,12,'#725a4c')
            + rect(x-4,y-15,8,8,'#493f3d')
            + rect(x-3,y-14,6,6,'#e5ad60')
            + rect(x-2,y-13,3,4,'#ffdf98')
            + rect(x-5,y-17,10,2,'#a87b57'))


def cloud(x, y, scale=1, opacity='.3'):
    return f'<g transform="translate({x},{y}) scale({scale})" opacity="{opacity}" fill="#7e9d9f"><path d="M0 8h9V3h13V0h17v6h15v5h10v5H0Z"/></g>'


def inside(x,y,polygon):
    hit = False
    for (a,b),(c,d) in zip(polygon,polygon[1:]+polygon[:1]):
        if (b>y) != (d>y) and x < (c-a)*(y-b)/(d-b)+a:
            hit=not hit
    return hit


def draw_garden(state, day, weather):
    rng=random.Random(1907)
    n=len(state['plots'])
    top=[(91,178),(238,104),(280,105),(499,210),(505,226),
         (362,300),(324,305),(93,198)]
    pieces=[f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 600 400" role="img" aria-labelledby="title desc">
<title id="title">Tiny world — {n} of 24 garden plots planted</title>
<desc id="desc">An original pixel-art island with a cottage, glowing lanterns, a waterfall and 24 planting plots. Use the labelled planting table below. Imaginary weather: {weather}.</desc>
<defs>
  <linearGradient id="sky" x2="0" y2="1"><stop stop-color="#101c2c"/><stop offset="1" stop-color="#244248"/></linearGradient>
  <radialGradient id="moon"><stop stop-color="#94b1b5" stop-opacity=".14"/><stop offset="1" stop-color="#94b1b5" stop-opacity="0"/></radialGradient>
  <radialGradient id="lamp"><stop stop-color="#ffd38a" stop-opacity=".4"/><stop offset="1" stop-color="#ffd38a" stop-opacity="0"/></radialGradient>
  <clipPath id="frame"><rect width="600" height="400" rx="12"/></clipPath>
</defs>
<style>.firefly{{animation:glimmer 5s ease-in-out infinite alternate}}.firefly:nth-of-type(even){{animation-delay:-2s}}@keyframes glimmer{{from{{opacity:.2}}to{{opacity:.85}}}}@media(prefers-reduced-motion:reduce){{.firefly{{animation:none}}}}</style>
<g clip-path="url(#frame)">
<rect width="600" height="400" fill="url(#sky)"/>
<circle cx="482" cy="88" r="145" fill="url(#moon)"/>
''']
    for _ in range(66):
        x,y=rng.randrange(20,580),rng.randrange(73,347)
        if not inside(x,y,top):
            pieces.append(rect(x,y,1,1,rng.choice(['#60818c','#52727e','#8fa9aa'])))
    pieces += [cloud(406,108,.9,'.13'),cloud(41,273,1.6,'.10'),cloud(455,307,1.5,'.13')]
    # Pixel crescent and a wandering cloud.
    pieces += [poly([(493,54),(505,54),(505,58),(513,58),(513,66),(517,66),(517,81),(513,81),(513,89),(505,89),(505,93),(489,93),(489,89),(481,89),(481,81),(477,81),(477,66),(481,66),(481,58),(493,58)],'#ecdec0'),
               poly([(501,53),(512,53),(512,58),(519,58),(519,78),(507,78),(507,74),(499,74),(499,66),(495,66),(495,58),(501,58)],'#172837'),cloud(493,96,.7,'.2')]
    pieces += [sprite('sprout',43,48,1.5),text(61,37,'TINY WORLD',15,'#f4e6ca','letter-spacing="3"'),
               text(61,53,'A garden we grow together.',8,'#99b2b6')]
    # Suspended rock, with stepped facets rather than smooth blobs.
    left=[(91,192),(333,301),(333,348),(311,348),(311,358),(269,347),(269,338),(239,338),(239,328),(207,320),(207,312),(178,306),(178,298),(146,282),(146,273),(122,263),(122,251),(105,242),(105,220),(91,214)]
    right=[(333,301),(505,219),(499,257),(487,257),(487,278),(470,283),(470,300),(445,309),(445,321),(411,330),(411,341),(371,350),(371,358),(333,348)]
    pieces += [poly(left,'#564b4b'),poly(right,'#343e45'),
               poly([(100,211),(325,313),(325,326),(216,280),(216,277),(150,249),(150,244),(100,223)],'#73604f'),
               poly([(338,315),(490,241),(490,252),(419,289),(419,297),(338,336)],'#465054'),
               poly([(280,294),(307,305),(296,332),(277,322)],'#423e46'),
               poly([(173,261),(192,270),(196,297),(178,289)],'#453f43'),
               poly([(405,290),(421,283),(414,319),(397,325)],'#283b42')]
    for _ in range(175):
        x,y=rng.randrange(100,497),rng.randrange(211,350)
        if inside(x,y,left) or inside(x,y,right):
            pieces.append(rect(x,y,rng.choice([2,3,5,7]),rng.choice([1,2,3]),rng.choice(['#8b7055','#645750','#413e46','#3b4449'])))
    # Grass rim and scattered square tufts.
    pieces += [poly([(x,y+7) for x,y in top],'#365b44'),poly([(x,y+3) for x,y in top],'#648655'),poly(top,'#78965e')]
    for _ in range(450):
        x,y=rng.randrange(94,502),rng.randrange(106,304)
        if inside(x,y,top):
            pieces.append(rect(x,y,rng.choice([1,2,3]),1,rng.choice(['#859f65','#93ac70','#637e52','#6c8b57'])))
    # The winding path connects the cottage and garden edge.
    for x,y in [(190,160),(207,170),(225,180),(243,190),(261,200),(280,210),(299,220),(317,230),(336,240),(355,250),(374,260)]:
        pieces += [diamond(x,y,12,5,'#657950'),diamond(x,y-1,10,4,'#b2ac7b'),rect(x-3,y-2,4,1,'#cebd8b')]
    # Tiny shed with sloped roof, chimney, window and warm doorway.
    pieces += [diamond(164,156,35,15,'#59754d'),
               poly([(140,127),(170,139),(170,161),(140,148)],'#b89768'),
               poly([(170,139),(192,129),(192,151),(170,161)],'#80694f'),
               poly([(135,126),(155,101),(176,110),(198,128),(170,142)],'#4d535d'),
               poly([(135,126),(155,101),(176,110),(158,134)],'#8b7170'),
               poly([(158,134),(176,110),(198,128),(170,142)],'#675a64'),
               poly([(133,126),(158,136),(171,144),(200,129),(200,132),(171,147),(133,130)],'#3f424b'),
               rect(176,105,7,13,'#8a7b69'),rect(175,103,9,3,'#b0a08b'),
               poly([(145,133),(154,137),(154,145),(145,141)],'#f1ca7f'),
               poly([(176,143),(184,139),(184,154),(176,158)],'#433f3d'),
               poly([(178,144),(183,142),(183,153),(178,155)],'#e4b36f'),
               rect(173,89,3,6,'#8b9b9a','opacity=".35"'),rect(168,80,5,5,'#8b9b9a','opacity=".2"')]
    # A few permanent trees frame the playable plots.
    pieces += [sprite('Pine',118,184,2),sprite('Pine',136,168,1.5),sprite('Oak',241,126,1.5)]
    # Garden plots follow the island's isometric grid and render back to front.
    plots=[]
    for r,row in enumerate('ABCD'):
        for c in range(6):
            x,y=282+(c-r)*29,145+(c+r)*14
            plots.append((y,x,f'{row}{c+1}',r,c))
    plot_markers=[]
    for y,x,plot,r,c in sorted(plots):
        plant=state['plots'].get(plot)
        title=f'{plot}: {plant["seed"]}, caretaker {plant["user"]}' if plant else f'{plot}: empty'
        pieces += [f'<g><title>{escape(title)}</title>',diamond(x,y+2,24,11,'#4d7048'),diamond(x,y,22,10,'#ae8c5a'),diamond(x,y-1,20,8,'#765640')]
        for offset in (-9,-3,3,9):
            pieces.append(poly([(x+offset-7,y-3),(x+offset+2,y+1),(x+offset+4,y),(x+offset-5,y-4)],'#956a48'))
        if plant:
            age=max(0,(day-date.fromisoformat(plant['planted'])).days)
            pieces.append(sprite('sprout' if age==0 else plant['seed'],x,y-1,1.5 if age<4 else 2))
        else:
            pieces += [rect(x-2,y-3,5,1,'#bd9765'),rect(x,y-5,1,5,'#bd9765')]
        # Plot IDs use small stakes on the right side, away from plant canopies.
        pieces += [rect(x+13,y+3,1,7,'#775d45'),'</g>']
        plot_markers += [rect(x+9,y,12,6,'#d3bd86'),text(x+15,y+5,plot,4.5,'#473f37','text-anchor="middle"')]
    pieces.extend(plot_markers)
    # Pond and spillway, at the outside edge of the island.
    pieces += [poly([(434,242),(448,235),(464,237),(478,244),(478,253),(459,262),(446,260),(431,252)],'#3d6c69'),
               poly([(438,242),(449,239),(463,241),(472,246),(469,252),(457,258),(444,254),(437,250)],'#659e9d'),
               rect(443,244,15,2,'#96c3b8'),rect(455,250,11,1,'#bdd9c6'),
               poly([(457,257),(466,253),(469,256),(464,286),(460,302),(451,326),(444,327),(452,298)],'#326976'),
               poly([(457,257),(461,256),(460,283),(456,305),(448,323),(445,325),(451,303)],'#76b5b9'),
               poly([(461,257),(464,255),(463,280),(460,294),(457,297),(459,282)],'#b2d9cd'),
               rect(445,329,7,2,'#7aafb0','opacity=".65"'),rect(438,334,17,2,'#6b9d9f','opacity=".35"')]
    # Fence, small flowers, rocks and warm lanterns add lived-in detail.
    for x,y in [(122,211),(144,221),(166,231),(188,241)]:
        pieces += [rect(x,y-13,3,15,'#a8885f'),poly([(x,y-11),(x+24,y),(x+24,y+3),(x,y-8)],'#ba9b68')]
    for x,y in [(100,194),(114,202),(383,275),(391,271),(405,261),(211,131)]:
        pieces += [rect(x,y-4,1,5,'#476d42'),rect(x-1,y-6,3,3,rng.choice(['#e7b16d','#e8c981','#d3949c']))]
    for x,y in [(308,292),(325,297),(407,270),(420,267)]:
        pieces += [poly([(x-4,y),(x-2,y-4),(x+3,y-4),(x+6,y),(x+2,y+3)],'#8b9a83'),rect(x-1,y-3,3,1,'#b9b99a')]
    pieces += [lantern(197,176),lantern(375,281)]
    for x,y in [(120,247),(354,112),(410,174),(78,228),(512,279),(197,309)]:
        pieces.append(f'<g class="firefly"><circle cx="{x}" cy="{y}" r="9" fill="url(#lamp)"/>'+rect(x,y,2,2,'#f1d490')+'</g>')
    if weather == 'Soft rain':
        for _ in range(28):
            x,y=rng.randrange(85,515),rng.randrange(90,290)
            pieces.append(rect(x,y,1,4,'#82afbd','opacity=".25"'))
    elif weather == 'Passing clouds':
        pieces += [cloud(331,98,.8,'.22'),cloud(58,119,.9,'.17')]
    pieces += [rect(31,366,538,1,'#456064'),text(32,385,f'{n:02d}/24 GROWING',8,'#e5d8b9'),
               text(172,385,f'{len(state["gardeners"]):02d} GARDENERS',8,'#a7bdb4'),
               text(568,385,weather.upper(),8,'#a7bdb4','text-anchor="end"'),'</g></svg>']
    return '\n'.join(pieces)


def project_cover(name, subtitle, kind):
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="230" viewBox="0 0 600 115" role="img"><title>{escape(name)} — {escape(subtitle)}</title>',
           '<rect width="600" height="115" rx="10" fill="#142631"/>',
           text(24,25,'ON THE WORKBENCH',6,'#8baa9f','letter-spacing="2"'),
           text(23,58,name,22,'#f1e3c8','font-weight="bold"'),text(24,80,subtitle,7,'#b3c7ba')]
    rng=random.Random(63)
    if kind=='terrain':
        for r in range(5):
            for c in range(7):
                x,y=452+(c-r)*11,22+(c+r)*5
                h=int(4+9*((c-3)**2+(r-2)**2)/13)
                parts += [diamond(x,y+3,10,5,'#3c6158'),diamond(x,y-h,10,5,['#88a971','#a4ba7b','#6e9264'][(c+r)%3])]
    elif kind=='yield':
        for c in range(9):
            x=417+c*15
            h=[18,26,21,36,41,33,50,46,62][c]
            parts += [rect(x,91-h,9,h,'#b5a366'),rect(x,91-h,5,h,'#e4c780'),rect(x,91-h-2,9,2,'#f2df9c')]
        parts.append(sprite('Wheat',539,39,1))
    else:
        for r in range(5):
            for c in range(8):
                x,y=412+c*18,17+r*17
                colors=['#426f5c','#7c9464','#b0a66e','#c89566','#c97956']
                parts.append(rect(x,y,16,15,colors[min(4,(c+r)//2)]))
                parts.append(rect(x+2,y+2,4,2,'#e0c595','opacity=".25"'))
    parts += [text(575,104,'↗',12,'#d5c598','text-anchor="end"'),'</svg>']
    return '\n'.join(parts)
