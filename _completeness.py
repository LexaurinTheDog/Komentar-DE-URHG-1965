from pathlib import Path
from lxml import html,etree as E
import re,json,hashlib,collections
W=Path(__file__).resolve().parent;S=W/'sources';r=html.fromstring((S/'index.html').read_bytes())
expected=[]
for a in r.xpath('//a[@href]'):
 h=a.get('href');m=re.fullmatch(r'__(\d+[a-z]?)\.html',h)
 if m: expected.append('p'+m.group(1))
 elif h=='anlage__zu___61a_.html':expected.append('anlage')
# Official HTML also represents the jointly repealed provisions in one link.
if 'p52a' not in expected and r.xpath('//a[contains(@href,"52a") or contains(text(),"52a und 52b")]'):expected+=['p52a','p52b']
expected=list(dict.fromkeys(expected))
xml=E.parse(str(S/'urhg.xml'));xmlids=[]
for n in xml.xpath('//norm[metadaten/enbez]'):
 s=n.findtext('metadaten/enbez','');m=re.fullmatch(r'§ (\d+[a-z]?)',s)
 if m:xmlids.append('p'+m.group(1))
 elif '52a und 52b' in s:xmlids+=['p52a','p52b']
 elif s.startswith('Anlage'):xmlids.append('anlage')
units=[json.loads(l) for l in (W/'units.jsonl').read_text().splitlines()];actual=[u['id'] for u in units]
rep=dict(official_index_url='https://www.gesetze-im-internet.de/urhg/index.html',expected_ids=expected,official_xml_ids=xmlids,parsed_ids=actual,expected_count=len(expected),parsed_count=len(actual),missing=sorted(set(xmlids)-set(actual)),unexpected=sorted(set(actual)-set(xmlids)),duplicates=[k for k,v in collections.Counter(actual).items() if v>1],index_xml_difference=sorted(set(expected)^set(xmlids)),annex_disposition=[dict(id='anlage',included=True,description='Anlage zu § 61a: alle fünf Quellengruppen mit ihren nummerierten und buchstabierten Suchquellen; eigenständige Einheit.')],empty_slots=json.loads((S/'xml-disposition.json').read_text()),hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [S/'urhg.xml',S/'index.html',W/'units.jsonl']})
rep['ok']=not any(rep[k] for k in ['missing','unexpected','duplicates','index_xml_difference']) and len(actual)==255
(W/'completeness-report.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n');print({k:rep[k] for k in ['expected_count','parsed_count','missing','unexpected','duplicates','index_xml_difference','ok']})
