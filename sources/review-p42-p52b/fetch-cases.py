from pathlib import Path
from urllib.request import urlopen,Request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from lxml import html
import json,hashlib,zipfile,io
D=Path(__file__).resolve().parent
urls={
'pelham-2026-lexuri.html':'https://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri=CELEX:62023CJ0590:DE:HTML',
'pelham-2026-plain.pdf':'https://eur-lex.europa.eu/legal-content/DE/TXT/PDF/?uri=CELEX:62023CJ0590',
'spiegel-online-plain.pdf':'https://eur-lex.europa.eu/legal-content/DE/TXT/PDF/?uri=CELEX:62017CJ0516',
'prca-plain.pdf':'https://eur-lex.europa.eu/legal-content/DE/TXT/PDF/?uri=CELEX:62013CJ0360',
'pelham-info.html':'https://infocuria.curia.europa.eu/tabs/affair?lang=de&publishedId=C-590%2F23&searchTerm=C-590%2F23',
'reformistischer.zip':'https://www.rechtsprechung-im-internet.de/jportal/docs/bsjrs/jb-KORE306052020.zip'}
def get(item):
 name,url=item;t=datetime.now(timezone.utc).isoformat()
 try:
  with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as r:b=r.read();code=r.status;headers=str(r.headers);final=r.url
  valid=False
  if name.endswith('.pdf'):valid=b.startswith(b'%PDF-')
  elif name.endswith('.zip'):
   valid=zipfile.is_zipfile(io.BytesIO(b))
   if valid:
    z=zipfile.ZipFile(io.BytesIO(b));xb=z.read(next(n for n in z.namelist() if n.endswith('.xml')));(D/'reformistischer.xml').write_bytes(xb)
  else:valid=b'<html' in b.lower() and (b'URTEIL' in b or name=='pelham-info.html')
  path=D/(name if valid else 'rejected-'+name+'.body');path.write_bytes(b);(D/(name+'.headers')).write_text(headers)
  if valid and name.endswith('.html'):(D/name.replace('.html','-official.txt')).write_text(html.fromstring(b).text_content())
  return dict(url=url,final_url=final,accessed_at=t,http_status=code,response_path=str(path.relative_to(D.parent.parent)),headers_path=str((D/(name+'.headers')).relative_to(D.parent.parent)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),expected_format_validated=valid)
 except Exception as e:return dict(url=url,accessed_at=t,error=str(e),expected_format_validated=False)
with ThreadPoolExecutor(max_workers=4) as p:res=list(p.map(get,urls.items()))
p=D/'case-fetch-results.json';old=json.loads(p.read_text());p.write_text(json.dumps(old+res,indent=2,ensure_ascii=False)+'\n');print(json.dumps(res,indent=2))
