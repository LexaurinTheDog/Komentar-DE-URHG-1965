#!/usr/bin/env python3
"""Reproducible extraction from the preserved official GII XML, not the intake prose."""
from pathlib import Path
from lxml import etree as E
import re,json,hashlib
W=Path(__file__).resolve().parent
S=W/'sources'; raw=S/'urhg.xml'; root=E.parse(str(raw)).getroot()
def txt(e):
    if e is None:return ''
    def rec(x):
        out=x.text or ''
        for c in x:
            if c.tag=='BR': t='\n'
            else:t=rec(c)
            if c.tag in ('P','DL'):t='\n\n'+t+'\n\n'
            elif c.tag=='DT':t='\n'+t+' '
            elif c.tag=='DD':t=t+'\n'
            out+=t+(c.tail or '')
        return out
    s=rec(e);s=re.sub(r'[ \t\r\f\v]+',' ',s);s=re.sub(r' *\n *','\n',s);return re.sub(r'\n{3,}','\n\n',s).strip()
chapters=[(1,'grundlagen','Werk, Urheber und Persönlichkeit',1),(2,'verwertung','Verwertungsrechte und weitere Befugnisse',15),(3,'rechtsverkehr','Rechtsnachfolge und Nutzungsverträge',28),(4,'schranken','Gesetzlich erlaubte Nutzungen und Vergütung',44.1),(5,'institutionen','Bildung, Forschung und Kulturerbe',60.1),(6,'schutzdauer-software','Schutzdauer und Computerprogramme',64),(7,'leistungsschutz','Ausgaben, Lichtbilder, Darbietungen, Tonträger und Sendungen',70),(8,'daten-presse-film','Datenbanken, Presse und Film',87.1),(9,'rechtsschutz','Technischer und zivilrechtlicher Rechtsschutz',95.1),(10,'strafrecht-vollstreckung','Strafrecht, Zoll und Zwangsvollstreckung',106),(11,'anwendung','Persönlicher Anwendungsbereich',120),(12,'uebergang','Übergangs- und Schlussrecht sowie Suchquellen',129)]
units=[];structures=[];dispositions=[]
for n in root:
    m=n.find('metadaten');g=m.find('gliederungseinheit');label=txt(m.find('enbez'));title=' '.join(txt(m.find('titel')).split())
    if g is not None:
        key=g.findtext('gliederungskennzahl'); h=' '.join((txt(g.find('gliederungsbez'))+' — '+txt(g.find('gliederungstitel'))).split())
        structures=[(k,v) for k,v in structures if len(k)<len(key)];structures.append((key,h));continue
    if not label or label=='Inhaltsübersicht':continue
    node=E.fromstring(E.tostring(n.find('textdaten/text/Content')))
    editorial=[txt(x) for x in node.findall('.//kommentar')]
    for x in node.findall('.//noindex'):x.getparent().remove(x)
    content=txt(node);notes=[txt(x) for x in n.findall('textdaten/fussnoten/Content') if txt(x)]
    notes+=editorial
    labels=['§ 52a','§ 52b'] if '52a und 52b' in label else [label]
    for lab in labels:
        annex=lab.startswith('Anlage'); match=re.fullmatch(r'§ (\d+)([a-z]?)',lab)
        if not (annex or match):raise ValueError(lab)
        ident='anlage' if annex else 'p'+match.group(1)+match.group(2)
        num=999 if annex else int(match.group(1))+(0.1 if match.group(2) else 0)
        chapter=max(c[0] for c in chapters if num>=c[3])
        body=content
        if not body:
            assert title=='(weggefallen)',(lab,title)
            body=title
            notes=notes+['Das amtliche XML enthält hier keinen Vorschriftentext; der Wegfallvermerk stammt aus dem amtlichen Titel.']
        units.append(dict(id=ident,label=lab,title=title,chapter=chapter,structure=[v for k,v in structures],text=body,notes=notes,official_doknr=n.get('doknr')))
        dispositions.append(dict(id=ident,doknr=n.get('doknr'),empty_body=not bool(content),repealed=title=='(weggefallen)',xml_text_sha256=hashlib.sha256(content.encode()).hexdigest()))
assert len(units)==255
(W/'units.jsonl').write_text(''.join(json.dumps(u,ensure_ascii=False)+'\n' for u in units))
canonical=['# Amtlich extrahierter konsolidierter Text des UrhG','Quelle: https://www.gesetze-im-internet.de/urhg/xml.zip',txt(root[0].find('textdaten/fussnoten'))]
for u in units:canonical += ['## '+u['label']+' '+u['title'],u['text'],*u['notes']]
(S/'urhg-canonical.md').write_text('\n\n'.join(canonical)+'\n')
meta=dict(cc='de',lang='de',repo='Komentar-DE-URHG-1965',repo_dir='/Volumes/LaCie/open-commentary/de/Komentar-DE-URHG-1965',title='Kommentar zum Urheberrechtsgesetz (UrhG)',source_path=str(S/'urhg-canonical.md'),intro_file='00-einleitung.md',intro_desc='Stand, Methode und Benutzung',labels=dict(text='Wortlaut der Vorschrift',chapter='Kommentarkapitel',notes='Amtlicher bzw. dokumentierter Quellenhinweis'),chapters=[dict(n=n,slug=slug,title=title) for n,slug,title,start in chapters],decisive_date='2026-10-19',official_xml=str(raw))
(W/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
(S/'xml-disposition.json').write_text(json.dumps(dispositions,ensure_ascii=False,indent=2)+'\n')
print('Extracted',len(units),'units; chapters',len(chapters))
