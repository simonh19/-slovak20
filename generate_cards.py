import json, re, urllib.request
from pypdf import PdfReader

PDF_URL='https://flashcardo.com/cdn/printable/german/Lernkarten-Einseitig-1000-Slowakisch-Deutsch.pdf'
PDF_FILE='flashcardo-1000.pdf'
urllib.request.urlretrieve(PDF_URL, PDF_FILE)
reader=PdfReader(PDF_FILE)

# The PDF has a few stray accessibility/category labels in its text layer.
# These are removed before pairing; the underlying source still provides the
# actual Slovak-German cards.
ARTEFACTS={
    'všeobecný','človek','zviera','jedlo','umenie','počasie','inteligencia',
    'topánka','dvere','matka','otec','telo','roh','budova','veľký','malý',
    'zámka','škola','nápoj','domov'
}
FOOTER=re.compile(r'©\s*20\d\d\s+Flashcardo\.com.*$',re.I)

def clean_line(s):
    s=FOOTER.sub('',s).strip()
    return re.sub(r'\s+',' ',s)

def category(sk,de):
    s=(sk+' '+de).lower()
    if any(x in s for x in ['hotel','zimmer','gast','rezeption','reserv','restaurant','bar','frühstück','kellner','rechnung','schlüssel','aufenthalt']): return 'Hotel & Service'
    if any(x in s for x in ['essen','brot','käse','fleisch','fisch','gemüse','obst','kaffee','bier','wein','wasser','suppe']): return 'Essen & Trinken'
    if any(x in s for x in ['arzt','krank','gesund','krankenhaus','medikament','schmerz','fieber']): return 'Gesundheit'
    if any(x in s for x in ['zug','bus','flugzeug','bahnhof','straße','auto','taxi','reise','reisen']): return 'Reisen'
    if any(x in s for x in ['haus','wohnung','küche','bad','bett','dusche','tür','fenster']): return 'Haus'
    if any(x in s for x in ['arbeit','job','firma','büro','geld','gehalt','kunde','geschäft']): return 'Arbeit'
    if any(x in s for x in ['schule','universität','prüfung','lehrer','buch','wissenschaft']): return 'Lernen'
    if any(x in s for x in ['sport','laufen','schwimmen','fußball','tennis','wandern']): return 'Sport'
    if any(x in s for x in ['tier','hund','katze','fisch','vogel','wald','berg','see','regen','sonne']): return 'Natur'
    return 'Alltag'

words=[]; seen=set()
for page in reader.pages:
    lines=[clean_line(x) for x in (page.extract_text() or '').splitlines()]
    lines=[x for x in lines if x and 'flashcardo.com' not in x.lower()]
    lines=[x for x in lines if x.casefold() not in ARTEFACTS]
    i=0
    while i+1<len(lines):
        sk,de=lines[i],lines[i+1]
        if len(sk)>80 or len(de)>100 or 'www.' in sk.lower() or 'www.' in de.lower() or '©' in sk or '©' in de:
            i+=2; continue
        if sk.lower() in {'copyright','deutsch','slowakisch'}:
            i+=2; continue
        key=sk.casefold()
        if key not in seen:
            seen.add(key); words.append({'id':'fc:'+key,'sk':sk,'de':de,'cat':category(sk,de),'source':'Flashcardo 1000 Slovak-German'})
        i+=2

# Fill only if the PDF text layer discarded a few cards.
with open('extra_cards.json',encoding='utf-8') as f: extras=json.load(f)
for de,sk in extras:
    if len(words)>=1000: break
    key=sk.casefold()
    if key in seen: continue
    seen.add(key); words.append({'id':'x:'+key,'sk':sk,'de':de,'cat':'Hotel & Service','source':'eigener Lernwortschatz'})

if len(words)<1000: raise RuntimeError(f'Only {len(words)} clean cards parsed from the 1000-card source')
words=words[:1000]
with open('cards.json','w',encoding='utf-8') as f: json.dump(words,f,ensure_ascii=False,separators=(',',':'))
print(f'Generated {len(words)} clean cards')
