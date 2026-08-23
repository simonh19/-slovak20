import json, re, ssl, urllib.request
from bs4 import BeautifulSoup
from pypdf import PdfReader

MAIN='https://flashcardo.com/de/slowakisch-lernkarten/'
PDF='https://flashcardo.com/cdn/printable/german/Lernkarten-Einseitig-1000-Slowakisch-Deutsch.pdf'
CTX=ssl._create_unverified_context()
UA='Mozilla/5.0 (compatible; Slovak20/1.0)'


def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA})
    with urllib.request.urlopen(req,context=CTX,timeout=30) as r:
        return r.read()


def clean(s):
    return re.sub(r'\s+',' ',s or '').strip()


def category(sk,de):
    s=(sk+' '+de).lower()
    groups={
      'Hotel & Service':['hotel','zimmer','gast','rezeption','reserv','restaurant','bar','frühstück','kellner','rechnung','schlüssel','aufenthalt','check-in','check-out'],
      'Essen & Trinken':['essen','brot','käse','fleisch','fisch','gemüse','obst','kaffee','bier','wein','wasser','suppe'],
      'Gesundheit':['arzt','krank','gesund','krankenhaus','medikament','schmerz','fieber','apotheke'],
      'Reisen':['zug','bus','flugzeug','bahnhof','straße','auto','taxi','reise','reisen','ticket','flughafen'],
      'Haus':['haus','wohnung','küche','bad','bett','dusche','tür','fenster'],
      'Arbeit':['arbeit','job','firma','büro','geld','gehalt','kunde','geschäft'],
      'Lernen':['schule','universität','prüfung','lehrer','buch','wissenschaft'],
      'Sport':['sport','laufen','schwimmen','fußball','tennis','wandern'],
      'Natur':['tier','hund','katze','vogel','wald','berg','see','regen','sonne']}
    for c,terms in groups.items():
        if any(t in s for t in terms): return c
    return 'Alltag'


def add(words,seen,sk,de,source):
    sk,de=clean(sk),clean(de)
    if not sk or not de or len(sk)>100 or len(de)>120: return
    if sk.lower() in {'slowakisch','deutsch','copyright'}: return
    if 'flashcardo.com' in sk.lower() or 'flashcardo.com' in de.lower(): return
    key=sk.casefold()
    if key in seen: return
    seen.add(key); words.append({'id':f'fc:{key}','sk':sk,'de':de,'cat':category(sk,de),'source':source})


def parse_html(words,seen):
    soup=BeautifulSoup(get(MAIN),'html.parser')
    links=[]
    for a in soup.find_all('a'):
        txt=clean(a.get_text(' ',strip=True))
        if re.fullmatch(r'(?:[1-9]\d{0,2})-(?:[1-9]\d{0,3})',txt):
            href=a.get('href')
            if href:
                if href.startswith('/'): href='https://flashcardo.com'+href
                links.append(href)
    for href in links:
        try:
            page=BeautifulSoup(get(href),'html.parser')
            for tr in page.find_all('tr'):
                cells=[clean(x.get_text(' ',strip=True)) for x in tr.find_all(['td','th'])]
                if len(cells)>=2 and cells[0] and cells[1] and not cells[0].isdigit():
                    add(words,seen,cells[0],cells[1],'Flashcardo Top 1000 Slovak-German')
        except Exception as e:
            print('subpage warning',href,e)


def parse_pdf(words,seen):
    try:
        data=get(PDF)
        with open('flashcardo-1000.pdf','wb') as f: f.write(data)
        reader=PdfReader('flashcardo-1000.pdf')
        for page in reader.pages:
            text=page.extract_text() or ''
            lines=[clean(x) for x in text.splitlines() if clean(x)]
            # First try obvious two-column text produced by pypdf layout mode.
            try:
                layout=page.extract_text(extraction_mode='layout') or ''
                layout_lines=[clean(x) for x in layout.splitlines() if clean(x)]
            except Exception:
                layout_lines=[]
            candidates=layout_lines or lines
            # Cards are printed as Slovak first, German second. Ignore page/footer labels.
            filtered=[]
            for x in candidates:
                xl=x.lower()
                if 'flashcardo.com' in xl or xl.startswith('©') or xl in {'slowakisch','deutsch'}: continue
                filtered.append(x)
            # Handle tab-separated columns first.
            for x in filtered:
                parts=[clean(p) for p in re.split(r'\t{1,}| {3,}',x) if clean(p)]
                if len(parts)>=2:
                    add(words,seen,parts[0],parts[1],'Flashcardo Top 1000 Slovak-German')
            # Fallback: pair neighbouring short lines when no cards were recovered from the page.
            if len(words)<1000:
                i=0
                while i+1<len(filtered):
                    a,b=filtered[i],filtered[i+1]
                    if len(a)<=80 and len(b)<=100:
                        add(words,seen,a,b,'Flashcardo Top 1000 Slovak-German')
                    i+=2
    except Exception as e:
        print('PDF warning',e)


words=[]; seen=set()
parse_html(words,seen)
if len(words)<1000: parse_pdf(words,seen)

# Keep the existing curated cards as a safety net, but never fabricate translations.
try:
    with open('extra_cards.json',encoding='utf-8') as f: extras=json.load(f)
    for de,sk in extras:
        if len(words)>=1000: break
        add(words,seen,sk,de,'eigener kuratierter Lernwortschatz')
except Exception:
    pass

if len(words)<1000:
    raise RuntimeError(f'Only {len(words)} clean Slovak-German cards available; refusing to pad with invented data')

words=words[:1000]
with open('cards.json','w',encoding='utf-8') as f:
    json.dump(words,f,ensure_ascii=False,separators=(',',':'))
print('Generated exactly',len(words),'clean Slovak-German cards')
