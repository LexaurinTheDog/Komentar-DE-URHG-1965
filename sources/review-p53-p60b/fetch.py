from pathlib import Path
from datetime import datetime,timezone
import urllib.request,json,hashlib,zipfile,io,concurrent.futures
from lxml import etree as E
W=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
jobs=[('current.zip','https://www.gesetze-im-internet.de/urhg/xml.zip'),('index.html','https://www.gesetze-im-internet.de/urhg/index.html'),('full.html','https://www.gesetze-im-internet.de/urhg/BJNR012730965.html'),('current.pdf','https://www.gesetze-im-internet.de/urhg/UrhG.pdf'),('amendment.pdf','https://www.recht.bund.de/bgbl/1/2026/157/regelungstext.pdf?__blob=publicationFile&v=1'),('aktuell.html','https://www.gesetze-im-internet.de/aktuDienst.html'),('moebelkatalog.zip','https://www.rechtsprechung-im-internet.de/jportal/docs/bsjrs/jb-KORE303392015.zip'),('drohnen.zip','https://www.rechtsprechung-im-internet.de/jportal/docs/bsjrs/jb-KORE310902024.zip')]
def fetch(job):
 name,url=job;at=datetime.now(timezone.utc).isoformat()
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'OpenCommentary-source-verification/1.0'}),timeout=45) as r:
   b=r.read();status=r.status;headers=dict(r.headers);final=r.url
  (D/name).write_bytes(b);(D/(name+'.headers.json')).write_text(json.dumps(headers,indent=2)+'\n')
  good=False
  if name.endswith('.zip'):
   z=zipfile.ZipFile(io.BytesIO(b));xml=[f for f in z.namelist() if f.endswith('.xml')];assert len(xml)==1
   xb=z.read(xml[0]);root=E.fromstring(xb);out=name[:-4]+'.xml';(D/out).write_bytes(xb)
   if name=='current.zip':assert root.tag=='dokumente' and 'UrhG' in root[0].xpath('./metadaten/jurabk/text()')
   else:assert root.tag=='dokument' and ('I ZR 177/13' if name.startswith('moebel') else 'I ZR 67/23') in ''.join(root.itertext())
   good=True
  elif name.endswith('.pdf'):good=b.startswith(b'%PDF-')
  else:good=b'<html' in b.lower() and (b'UrhG' in b or b'Aktualit' in b)
  return dict(url=url,final_url=final,accessed_at=at,response_received_at=datetime.now(timezone.utc).isoformat(),http_status=status,response_path=str((D/name).relative_to(W)),headers_path=str((D/(name+'.headers.json')).relative_to(W)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),expected_format_validated=good)
 except Exception as e:return dict(url=url,accessed_at=at,error=str(e),expected_format_validated=False)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(fetch,jobs))
(D/'fetch-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(results,ensure_ascii=False,indent=2))
