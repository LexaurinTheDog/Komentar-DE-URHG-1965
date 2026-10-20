#!/usr/bin/env python3
"""Independently enumerate official XML records and HTML links, then compare the parser output."""
from pathlib import Path
from lxml import html,etree as E
from collections import Counter
import re,json,hashlib
W=Path(__file__).resolve().parent;S=W/'sources';D=S/'preflight-2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def squash(s):return re.sub(r'\s+','',s)
def unit_id(label):
 m=re.fullmatch(r'§ (\d+[a-z]?)',label)
 if m:return 'p'+m.group(1)
 if label=='(XXXX) §§ 52a und 52b':return 'p52a-52b'
 if label=='Anlage (zu § 61a)':return 'anlage'
 raise ValueError('Unclassified official unit: '+label)
root=E.parse(str(S/'urhg.xml')).getroot();official=[];classification=[];annexes=[]
for n in root:
 m=n.find('metadaten');label=m.findtext('enbez');body=n.find('textdaten/text/Content')
 if m.find('gliederungseinheit') is not None:kind='structure'
 elif label=='Inhaltsübersicht':kind='table_of_contents'
 elif label:
  kind='annex' if label.startswith('Anlage') else 'statutory_unit'
  official.append(dict(id=unit_id(label),label=label,doknr=n.get('doknr'),title=''.join(m.find('titel').itertext()) if m.find('titel') is not None else '',body_empty=body is None or not ''.join(body.itertext()).strip()))
 else:
  kind='law_metadata_and_editorial_notes'
  assert body is None or not ''.join(body.itertext()).strip(),'Unlabelled operative text must be included'
 classification.append(dict(doknr=n.get('doknr'),label=label,disposition=kind))
 if kind=='annex':
  children=[]
  for group in body.xpath('./P/DL/DT'):
   number=''.join(group.itertext()).strip();dd=group.getnext();assert dd.tag=='DD'
   letters=[(''.join(dt.itertext()).strip(),''.join(dt.getnext().itertext())) for dt in dd.xpath('./LA/DL/DT')]
   children.append(dict(number=number,child_ids=['anlage/'+number.rstrip('.')+'/'+x[0].rstrip(')') for x in letters],letter_labels=[x[0] for x in letters]))
  annexes.append(dict(id=unit_id(label),label=label,doknr=n.get('doknr'),included=True,evidence_path='sources/urhg.xml',evidence_sha256=sha(S/'urhg.xml'),groups=children,description='Eine operative Anlage: fünf Quellengruppen; Buchstaben a–e, a–e, a–c, a–h und a–e. Fundstellenkommentar ist redaktioneller Hinweis, kein Tatbestand.'))
# HTML enumeration does not depend on the parsed units or XML enumeration.
index=html.fromstring((D/'index.html').read_bytes());indexids=[]
for a in index.xpath('//a[@href]'):
 h=a.get('href');m=re.fullmatch(r'__(\d+[a-z]?)\.html',h)
 if m:indexids.append('p'+m.group(1))
 elif h=='___52a_und_52b.html':indexids.append('p52a-52b')
 elif h=='anlage__zu___61a_.html':indexids.append('anlage')
units=[json.loads(l) for l in (W/'units.jsonl').read_text().splitlines()];actual=[u['id'] for u in units];expected=[o['id'] for o in official]
byid={u['id']:u for u in units};xmltext_errors=[]
for o in official:
 if o['id'] not in byid:continue
 n=next(n for n in root if n.get('doknr')==o['doknr']);body=E.fromstring(E.tostring(n.find('textdaten/text/Content')))
 for x in body.xpath('.//noindex'):x.getparent().remove(x)
 text=''.join(body.itertext()).strip() or o['title']
 u=byid[o['id']]
 if squash(text)!=squash(u['text']) or u['label']!=o['label'] or u['official_doknr']!=o['doknr']:xmltext_errors.append(o['id'])
for a in annexes:
 u=byid.get(a['id']);a['full_xml_text_agrees']=u is not None and a['id'] not in xmltext_errors
# The current official consolidation contains no Eingangsformel in any of these three formats.
full=html.fromstring((D/'full.html').read_bytes());pdftext=(D/'current-pdf.txt').read_text()
formula=dict(xml_record_present=any('Eingangsformel' in (n.findtext('metadaten/enbez') or '') for n in root),html_heading_present=any('Eingangsformel' in x.text_content() for x in full.xpath('//h3')),pdf_label_present='Eingangsformel' in pdftext,unclassified_operative_xml_records=[],disposition='Keine Eingangsformel im amtlichen konsolidierten XML, im vollständigen HTML oder im GII-PDF ausgewiesen. Der einzige unbenannte XML-Datensatz enthält ausschließlich Metadaten und Fußnoten, keinen Normkörper. Keine historische Formel aus Erinnerung ergänzt.',evidence_paths=['sources/urhg.xml','sources/preflight-2026-10-20/full.html','sources/preflight-2026-10-20/current-pdf.txt'])
rep=dict(official_xml_url='https://www.gesetze-im-internet.de/urhg/xml.zip',official_index_url='https://www.gesetze-im-internet.de/urhg/index.html',expected_ids=expected,official_identifiers=official,official_index_ids=indexids,parsed_ids=actual,expected_count=len(expected),parsed_count=len(actual),missing=sorted(set(expected)-set(actual)),unexpected=sorted(set(actual)-set(expected)),duplicates=[k for k,v in Counter(actual).items() if v>1],official_duplicate_ids=[k for k,v in Counter(expected).items() if v>1],official_duplicate_doknr=[k for k,v in Counter(n.get('doknr') for n in root).items() if v>1],index_duplicates=[k for k,v in Counter(indexids).items() if v>1],index_xml_difference=sorted(set(indexids)^set(expected)),order_agrees=actual==expected==indexids,independent_xml_stream_mismatches=xmltext_errors,annex_disposition=annexes,eingangsformel=formula,empty_slots=[o for o in official if o['body_empty'] or o['title']=='(weggefallen)' or byid.get(o['id'],{}).get('text')=='-'],xml_record_classification=classification,xml_record_counts=dict(Counter(x['disposition'] for x in classification)),historical_version_check=dict(all_builddates=sorted(set(n.get('builddate') for n in root)),duplicate_versions_found=False,scope='Aktuelle konsolidierte amtliche XML-Datei vollständig auf Mehrfachkennungen und unklassifizierte Normkörper geprüft; historische Datumsangaben in Übergangsrecht und Fußnoten sind keine daneben geltenden Fassungsdatensätze. Kein Vollarchiv aller seit 1965 geltenden Fassungen.'),hashes={str(p.relative_to(W)):sha(p) for p in [S/'urhg.xml',D/'index.html',D/'full.html',D/'current-pdf.txt',W/'units.jsonl']})
rep['ok']=not any(rep[k] for k in ['missing','unexpected','duplicates','official_duplicate_ids','official_duplicate_doknr','index_duplicates','index_xml_difference','independent_xml_stream_mismatches']) and rep['order_agrees'] and all(a['full_xml_text_agrees'] for a in annexes)
(W/'completeness-report.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:rep[k] for k in ['expected_count','parsed_count','missing','unexpected','duplicates','index_xml_difference','independent_xml_stream_mismatches','xml_record_counts','ok']},ensure_ascii=False))
raise SystemExit(0 if rep['ok'] else 1)
