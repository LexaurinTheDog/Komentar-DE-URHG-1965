from pathlib import Path
import urllib.request,datetime,hashlib,json
from lxml import html
W=Path(__file__).resolve().parent.parent;S=W/'sources';logs=[]
for celex,name in [('62011CJ0128','usedsoft'),('62017CJ0683','cofemel'),('62017CJ0516','spiegel-online'),('62013CJ0201','deckmyn')]:
 url='https://eur-lex.europa.eu/legal-content/DE/TXT/HTML/?uri=CELEX:'+celex
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'OpenCommentary source verification'})
  with urllib.request.urlopen(req,timeout=45) as r:body=r.read();status=r.status;headers=dict(r.headers)
  doc=html.fromstring(body);text='\n'.join(x.strip() for x in doc.itertext() if x.strip())
  valid=celex[1:5] in text and len(text)>15000 and ('URTEIL' in text or 'Urteil' in text)
  if not valid:raise ValueError('Unexpected or incomplete judicial body')
  (S/(name+'.html')).write_bytes(body);(S/(name+'.txt')).write_text(text)
  logs.append(dict(url=url,accessed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),http_status=status,sha256=hashlib.sha256(body).hexdigest(),raw_path='sources/'+name+'.html',text_path='sources/'+name+'.txt',format_validated=True))
 except Exception as e:logs.append(dict(url=url,error=str(e),accessed_at=datetime.datetime.now(datetime.timezone.utc).isoformat()))
(S/'authority-fetch.json').write_text(json.dumps(logs,indent=2));print(json.dumps(logs,indent=2))
