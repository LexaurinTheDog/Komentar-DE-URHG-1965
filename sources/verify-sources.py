#!/usr/bin/env python3
"""Verify preserved response integrity; access timestamps come from fetch logs, never mtimes.
To fetch anew run sources/preflight-2026-10-20/fetch.py explicitly, then re-evaluate version evidence.
"""
from pathlib import Path
import hashlib,json,zipfile
from lxml import etree as E
W=Path(__file__).resolve().parent.parent
v=json.loads((W/'sources/verification.json').read_text());errors=[]
for c in v['checks']:
 p=W/c['response_path']
 if hashlib.sha256(p.read_bytes()).hexdigest()!=c['sha256']:errors.append(str(p))
 if p.suffix=='.zip' and not zipfile.is_zipfile(p):errors.append('Invalid ZIP: '+str(p))
 if p.suffix=='.pdf' and not p.read_bytes().startswith(b'%PDF-'):errors.append('Invalid PDF: '+str(p))
r=E.parse(str(W/'sources/urhg.xml')).getroot()
assert r.tag=='dokumente' and r.findtext('.//jurabk')=='UrhG'
print(json.dumps(dict(response_bodies_checked=len(v['checks']),errors=errors,ok=not errors),ensure_ascii=False))
raise SystemExit(bool(errors))
