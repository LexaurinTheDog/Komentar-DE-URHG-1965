from pathlib import Path
from datetime import datetime,timezone
import requests,json,hashlib,zipfile,io
from lxml import etree as E
D=Path(__file__).resolve().parent; W=D.parent.parent; records=[]
jobs=[('current.zip','https://www.gesetze-im-internet.de/urhg/xml.zip','zip'),('index.html','https://www.gesetze-im-internet.de/urhg/index.html','html'),('amendment.pdf','https://www.recht.bund.de/bgbl/1/2026/157/regelungstext.pdf?__blob=publicationFile&v=1','pdf'),('boot.zip','https://www.rechtsprechung-im-internet.de/jportal/docs/bsjrs/jb-KORE304212021.zip','casezip')]
for name,url,fmt in jobs:
 start=datetime.now(timezone.utc).isoformat();r=requests.get(url,timeout=40);r.raise_for_status();b=r.content
 if fmt in ('zip','casezip'):
  z=zipfile.ZipFile(io.BytesIO(b));xs=[x for x in z.namelist() if x.endswith('.xml')];assert len(xs)==1
  raw=z.read(xs[0]);root=E.fromstring(raw)
  if fmt=='zip':assert root.tag=='dokumente' and 'UrhG' in root.xpath('//jurabk/text()')
  else:assert 'I ZR 9/18' in ''.join(root.itertext())
  (D/('current.xml' if fmt=='zip' else 'boot.xml')).write_bytes(raw)
 elif fmt=='pdf':assert b.startswith(b'%PDF-')
 else:assert b'UrhG' in b and b'<html' in b.lower()
 p=D/name;p.write_bytes(b);hp=D/(name+'.headers.json');hp.write_text(json.dumps(dict(r.headers),indent=2)+'\n')
 records.append(dict(url=url,final_url=r.url,accessed_at=start,response_received_at=datetime.now(timezone.utc).isoformat(),http_status=r.status_code,response_path=str(p.relative_to(W)),headers_path=str(hp.relative_to(W)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),expected_format_validated=True))
(D/'fetch-results.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');print(json.dumps(records,ensure_ascii=False))
