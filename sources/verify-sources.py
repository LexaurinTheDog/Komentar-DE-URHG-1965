from pathlib import Path
import json,hashlib,datetime,re,sys,shutil
from lxml import etree as E
sys.dont_write_bytecode=True
W=Path(__file__).resolve().parent.parent;S=W/'sources';sys.path.insert(0,'/Volumes/LaCie/open-commentary/_tools');from validate import norm
urls={'aktualitaet.html':'https://www.gesetze-im-internet.de/aktuDienst.html','urhg.zip':'https://www.gesetze-im-internet.de/urhg/xml.zip','index.html':'https://www.gesetze-im-internet.de/urhg/index.html','aktuell.html':'https://www.gesetze-im-internet.de/aktuell.html','bgbl-2026-157.html':'https://www.recht.bund.de/bgbl/1/2026/157/VO.html','bgbl-2026-157.pdf':'https://www.recht.bund.de/bgbl/1/2026/157/regelungstext.pdf?__blob=publicationFile&v=1','geburtstagszug.zip':'https://www.rechtsprechung-im-internet.de/jportal/docs/bsjrs/jb-KORE301962013.zip'}
headers={'aktualitaet.html':'aktualitaet.headers','urhg.zip':'urhg-xml.headers','index.html':'index.headers','aktuell.html':'aktuell.headers','bgbl-2026-157.html':'bgbl-2026-157.headers','bgbl-2026-157.pdf':'bgbl-2026-157-pdf.headers','geburtstagszug.zip':'geburtstagszug.headers'}
checks=[]
for name,url in urls.items():
 p=S/name;b=p.read_bytes();h=(S/headers[name]).read_text();statuses=re.findall(r'^HTTP/\S+ (\d+)',h,re.M)
 valid=(b.startswith(b'PK') if name.endswith('zip') else b.startswith(b'%PDF-') if name.endswith('pdf') else b'<html' in b.lower() or b'<!doctype html' in b.lower())
 checks.append(dict(url=url,accessed_at=datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat(),http_status=int(statuses[-1]),response_path='sources/'+name,headers_path='sources/'+headers[name],sha256=hashlib.sha256(b).hexdigest(),expected_format_validated=valid,bytes=len(b)))
root=E.parse(str(S/'urhg.xml'));assert root.findtext('.//jurabk')=='UrhG'
checks.append(dict(url=urls['urhg.zip'],response_path='sources/urhg.xml',sha256=hashlib.sha256((S/'urhg.xml').read_bytes()).hexdigest(),expected_format_validated=True,format='XML: dokumente, jurabk UrhG, doknr BJNR012730965',derived_from='sources/urhg.zip'))
u=[json.loads(l) for l in (W/'units.jsonl').read_text().splitlines()];original=norm((S/'intake-2026-10-02.md').read_text());missing=[]
for x in u:
 for p in re.split(r'\n\s*\n',x['text']):
  if len(norm(p))>=12 and norm(p) not in original:missing.append(dict(id=x['id'],paragraph=p))
change=dict(original_path='/Volumes/LaCie/law-intake/eu/de/gesetze/gii-urhg.md',preserved_copy='sources/intake-2026-10-02.md',original_sha256=hashlib.sha256((S/'intake-2026-10-02.md').read_bytes()).hexdigest(),original_retrieved_at='2026-10-02T00:40:25Z',official_builddate=root.getroot().get('builddate'),official_latest_change=root.findtext('.//standkommentar'),paragraphs_not_found_in_intake=missing,result='Keine Wortlautabweichung der extrahierten Vorschriften gegenüber der Aufnahme festgestellt.' if not missing else 'Abweichungen einzeln prüfen',latest_amendment=dict(citation='Art. 2 G v. 26.5.2026, BGBl. 2026 I Nr. 157',promulgated='2026-05-29',effective='2026-05-30',evidence='sources/bgbl-2026-157.txt',changes=['§ 54d: Aktualisierung des Verweises auf das Umsatzsteuergesetz.','§ 87b Abs. 3: Ausnahme nach Art. 43 der Verordnung (EU) 2023/2854.']))
(S/'change-map.json').write_text(json.dumps(change,ensure_ascii=False,indent=2)+'\n')
rep=dict(decisive_date='2026-10-19',verified_on=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=checks,version=change['official_latest_change'],effective_version_evidence='BGBl. 2026 I Nr. 157, Art. 2 und Art. 3, Seiten 7–8; verkündet 29.05.2026, wirksam 30.05.2026.',currency_check='Amtliche konsolidierte XML-Fassung und amtliches Inhaltsverzeichnis am 19.10.2026 abgerufen; jüngster ausgewiesener Änderungsstand mit Verkündung abgeglichen; zusätzlich amtliche Aktualitäten und dokumentierte Websuche geprüft. Keine spätere Änderung oder noch ausstehende Inkrafttretensregel in diesen Quellen gefunden.',limitations=['Die Recherche ist eine datierte Bestandsprüfung, keine Zusicherung künftiger Unverändertheit.'],change_map='sources/change-map.json')
(S/'verification.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n');print('Verified',len(checks),'responses; intake deviations',len(missing))
