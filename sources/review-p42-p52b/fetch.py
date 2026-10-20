from pathlib import Path
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib,json,zipfile,io
from lxml import etree as E,html
D=Path(__file__).resolve().parent
urls={
'current.zip':'https://www.gesetze-im-internet.de/urhg/xml.zip',
'index.html':'https://www.gesetze-im-internet.de/urhg/index.html',
'full.html':'https://www.gesetze-im-internet.de/urhg/BJNR012730965.html',
'aktuell.html':'https://www.gesetze-im-internet.de/aktuDienst.html',
'amendment.pdf':'https://www.recht.bund.de/bgbl/1/2026/157/regelungstext.pdf?__blob=publicationFile&v=1',
'current.pdf':'https://www.gesetze-im-internet.de/urhg/UrhG.pdf'}
def get(item):
 name,url=item;t=datetime.now(timezone.utc).isoformat()
 try:
  with urlopen(Request(url,headers={'User-Agent':'OpenCommentary-source-verification/1.0'}),timeout=45) as r:b=r.read();code=r.status;headers=str(r.headers);final=r.url
  (D/name).write_bytes(b);(D/(name+'.headers')).write_text(headers)
  if name.endswith('.zip'):
   assert zipfile.is_zipfile(io.BytesIO(b));z=zipfile.ZipFile(io.BytesIO(b));files=[n for n in z.namelist() if n.endswith('.xml')];assert len(files)==1
   xb=z.read(files[0]);root=E.fromstring(xb);assert root.tag=='dokumente' and root.findtext('.//jurabk')=='UrhG'
   (D/'current.xml').write_bytes(xb)
  elif name.endswith('.pdf'):assert b.startswith(b'%PDF-')
  else:
   h=html.fromstring(b);assert h.tag=='html';assert ('UrhG' in h.text_content() or 'Aktualitätendienst' in h.text_content())
  return dict(url=url,final_url=final,accessed_at=t,http_status=code,response_path=str((D/name).relative_to(D.parent.parent)),headers_path=str((D/(name+'.headers')).relative_to(D.parent.parent)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),expected_format_validated=True)
 except Exception as e:return dict(url=url,accessed_at=t,error=str(e),expected_format_validated=False)
with ThreadPoolExecutor(max_workers=4) as pool:checks=list(pool.map(get,urls.items()))
(D/'fetch-results.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
for c in checks:print(c)
