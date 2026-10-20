from pathlib import Path
from datetime import datetime,timezone
from lxml import html
import subprocess,json,hashlib
D=Path(__file__).resolve().parent; records=[]
for stem,celex in [('mio','62023CJ0580'),('renckhoff','62017CJ0161')]:
 url='https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:'+celex
 started=datetime.now(timezone.utc).isoformat()
 p=D/(stem+'-firecrawl.json')
 # Obtain a clocked response; preserve the earlier unclocked discovery snapshot.
 previous=D/(stem+'-discovery.json')
 if not previous.exists():previous.write_bytes(p.read_bytes())
 result=subprocess.run(['firecrawl','scrape',url,'--format','markdown,rawHtml','-o',str(p)],capture_output=True,text=True,timeout=55)
 end=datetime.now(timezone.utc).isoformat();assert result.returncode==0,result.stderr
 x=json.loads(p.read_text());m=x['metadata'];assert m['statusCode']==200
 h=html.fromstring(x['rawHtml']);body=h.xpath('//*[@id="document1"]');assert len(body)==1
 text='\n'.join(t.strip() for t in body[0].itertext() if t.strip());assert 'URTEIL DES GERICHTSHOFS' in text and ('Mio' in text if stem=='mio' else 'Renckhoff' in text)
 raw=D/(stem+'-raw.html');raw.write_text(x['rawHtml']);(D/(stem+'-full.txt')).write_text(text)
 records.append(dict(url=url,accessed_at=started,response_received_at=end,http_status=m['statusCode'],transport='Firecrawl CLI; statusCode reported by provider',cache_state=m.get('cacheState'),cache_timestamp=m.get('cachedAt'),response_path=str(p.relative_to(D.parent.parent)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),raw_path=str(raw.relative_to(D.parent.parent)),raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),expected_format_validated=True,format='Full official judgment HTML with document1, parties, numbered reasons and operative part',celex=celex))
(D/'case-fetch-results.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');print(json.dumps(records,ensure_ascii=False))
