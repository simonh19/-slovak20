import json,re,html,urllib.request
from bs4 import BeautifulSoup

URL='https://www.vokipedia.de/index.php?title=DEU%3ASlowakisch%3AGrundwortschatz'
with urllib.request.urlopen(URL,timeout=30) as r:
    page=r.read().decode('utf-8','replace')

soup=BeautifulSoup(page,'html.parser')
words=[]
seen=set()

def clean(s):
    s=html.unescape(s)
    s=re.sub(r'\([^)]*\)','',s)
    s=re.sub(r'\s+',' ',s).strip(' .,:;')
    return s

for table in soup.find_all('table'):
    rows=table.find_all('tr')
    for row in rows:
        cells=[clean(c.get_text(' ',strip=True)) for c in row.find_all(['td','th'])]
        if len(cells)<2 or cells[0] in ('Slowakisch','Deutsch'):
            continue
        sk,de=cells[0],cells[1]
        if not sk or not de or sk.lower()=='slowakisch' or de.lower()=='deutsch':
            continue
        if len(sk)>45 or len(de)>70: continue
        if any(x in sk.lower() for x in ['(music','((','_']): continue
        key=sk.lower()
        if key in seen: continue
        seen.add(key)
        words.append({'id':'v:'+key,'sk':sk,'de':de,'cat':'Grundwortschatz','source':'Vokipedia CC BY-SA'})

with open('extra_cards.json',encoding='utf-8') as f:
    extras=json.load(f)
for de,sk in extras:
    key=sk.lower()
    if key in seen: continue
    seen.add(key)
    words.append({'id':'x:'+key,'sk':sk,'de':de,'cat':'Hotel & Service','source':'eigener Lernwortschatz'})

# Remove a few clearly unsuitable legacy translations.
bad={'mäsiar':'Metzgerei','zmenáreň':'Wechselgeld','očakávať':'warten','opovážiť sa':'lieb','chudobný':'arm','dozadu':'rückwärts'}
words=[w for w in words if not (w['sk'].lower() in bad and w['de'].lower()==bad[w['sk'].lower()].lower())]

# Prefer the first 1000 clean cards; Vokipedia provides the A1 base and the extras cover hotel/service gaps.
words=words[:1000]
assert len(words)>=1000, f'Only {len(words)} cards available'

with open('cards.json','w',encoding='utf-8') as f:
    json.dump(words,f,ensure_ascii=False,separators=(',',':'))
print('Generated',len(words),'cards')
