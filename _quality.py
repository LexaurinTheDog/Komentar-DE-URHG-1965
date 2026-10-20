#!/usr/bin/env python3
from pathlib import Path
from lxml import etree as E
import re,json,collections,hashlib,datetime,itertools,difflib
W=Path(__file__).resolve().parent;meta=json.loads((W/'meta.json').read_text());O=Path(meta['repo_dir']);units=[json.loads(l) for l in (W/'units.jsonl').read_text().splitlines()];ids=[u['id'] for u in units]
blocks=[]
for p in sorted((W/'commentary').glob('*.md')):
 a=re.split(r'^=== (\S+)\s*$',p.read_text(),flags=re.M)
 blocks.extend((a[i],a[i+1].strip()) for i in range(1,len(a),2))
counts=collections.Counter(k for k,v in blocks);comments=dict(blocks)
# Independent XML stream comparison: ignore formatting whitespace only, not spelling/punctuation.
r=E.parse(str(W/'sources/urhg.xml'));expected={}
for n in r.xpath('//norm[metadaten/enbez]'):
 lab=n.findtext('metadaten/enbez');m=re.fullmatch(r'§ (\d+[a-z]?)',lab or '')
 keys=['p'+m.group(1)] if m else ['p52a-52b'] if '52a und 52b' in (lab or '') else ['anlage'] if (lab or '').startswith('Anlage') else []
 if not keys:continue
 c=E.fromstring(E.tostring(n.find('textdaten/text/Content')))
 for x in c.xpath('.//noindex'):x.getparent().remove(x)
 txt=''.join(c.itertext()).strip()
 if not txt:txt=n.findtext('metadaten/titel')
 for k in keys:expected[k]=txt
compact=lambda s:re.sub(r'\s+','',s)
text_errors=[u['id'] for u in units if compact(u['text'])!=compact(expected[u['id']])]
paragraphs=collections.defaultdict(list)
for k,v in blocks:
 for p in v.split('\n\n'):
  if len(p)>100:paragraphs[p].append(k)
repeated=[dict(ids=v,text=k) for k,v in paragraphs.items() if len(v)>1]
# Similarity on complete unit prose, independently of length checks.
near=[]
shingles={k:set(tuple(re.findall(r"\w+",v.lower())[i:i+5]) for i in range(max(0,len(re.findall(r"\w+",v.lower()))-4))) for k,v in blocks}
for (a,ta),(b,tb) in itertools.combinations(blocks,2):
 sa,sb=shingles[a],shingles[b];score=len(sa&sb)/max(1,len(sa|sb))
 if score>.12:near.append(dict(a=a,b=b,shared_five_word_shingles=round(score,4)))
links=[];bad=[]
for p in list(O.glob('*.md'))+list((O/'cases').glob('*.md')):
 for m in re.finditer(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
  href=m.group(1).split(' "')[0].strip('<>')
  if re.match(r'^[a-zA-Z]+:',href) or href.startswith('#'):continue
  dest=p.parent/href.split('#')[0];links.append(dict(file=p.name,target=href))
  if not dest.exists():bad.append(links[-1])
invalid_refs=[]
for k,v in blocks:
 for m in re.finditer(r'(?<!§)§\s+(\d+[a-z]?)\b',v):
  # External references in prose are deliberately not asserted as internal.
  tail=v[m.end():m.end()+80]
  if re.match(r'\s*(?:Abs\.?\s*\d+\s*)?(?:BGB|StGB|EGBGB|ZPO|des Bürgerlichen|des Verwertungsgesellschaften)',tail):continue
  if 'p'+m.group(1) not in ids and m.group(1) not in {'52a','52b'}:invalid_refs.append(dict(id=k,reference=m.group(0)))
short=[dict(id=u['id'],chars=len(comments.get(u['id'],''))) for u in units if len(comments.get(u['id'],''))<(120 if len(u['text'])<160 else 400)]
rep=dict(checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),units=len(units),commented_units=sum(bool(comments.get(k)) for k in ids),commentary_chars=sum(len(x) for x in comments.values()),duplicate_commentary_ids=[k for k,v in counts.items() if v>1],missing_commentary_ids=sorted(set(ids)-set(comments)),extra_commentary_ids=sorted(set(comments)-set(ids)),independent_xml_stream_mismatches=text_errors,identical_paragraphs_over_100_chars=repeated,similar_unit_pairs_shingle_jaccard_over_012=near,local_links_checked=len(links),broken_local_links=bad,unresolved_internal_references=invalid_refs,short_commentaries=short,ordinary_length_distribution=dict(under_700=sum(len(v)<700 for k,v in blocks),at_least_700=sum(len(v)>=700 for k,v in blocks)),limitations=['Ähnlichkeit ist nur ein maschineller Hinweis; keine Zertifizierung juristischer Originalität oder Richtigkeit.','Externe URLs werden anhand der dokumentierten Abrufe geprüft; keine Vollverlinkung amtlicher Roh-HTML-Navigation.'])
rep['ok']=not any(rep[k] for k in ['duplicate_commentary_ids','missing_commentary_ids','extra_commentary_ids','independent_xml_stream_mismatches','identical_paragraphs_over_100_chars','broken_local_links','unresolved_internal_references','short_commentaries'])
(W/'quality-report.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n');print(json.dumps(rep,ensure_ascii=False,indent=2))
