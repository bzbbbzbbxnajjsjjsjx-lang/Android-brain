#!/usr/bin/env python3
"""Fetch a public registered Material.io URL without bypassing access controls.

Only response metadata and SHA-256 are saved; page bodies are not retained.
Content verification always requires a separate human-authored review record.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
class Text(HTMLParser):
    def __init__(self):super().__init__();self.skip=0;self.title=False;self.in_title=False;self.data=[];self.title_text=[];self.description=""
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in {"script","style","noscript"}:self.skip+=1
        if tag=="title":self.in_title=True
        if tag=="meta" and a.get("name"," ").lower()=="description":self.description=a.get("content","")
    def handle_endtag(self,tag):
        if tag in {"script","style","noscript"} and self.skip:self.skip-=1
        if tag=="title":self.in_title=False
    def handle_data(self,data):
        value=" ".join(data.split())
        if not value:return
        if self.in_title:self.title_text.append(value)
        if not self.skip:self.data.append(value)
def fetch(url:str)->dict:
    sitemap=json.loads((ROOT/"routing/material3-sitemap-evidence.json").read_text())
    if url not in set(sitemap["urls"]):raise ValueError("URL is not in the recorded official Material sitemap; refusing unregistered retrieval")
    request=Request(url,headers={"User-Agent":"Android-Context-Harness-P6/1.0 public documentation retrieval"})
    retrieved=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    try:
        with urlopen(request,timeout=25) as response:
            body=response.read(4*1024*1024+1)
            if len(body)>4*1024*1024:raise ValueError("response exceeded 4 MiB safety limit")
            status=response.status;final=response.geturl();ctype=response.headers.get("Content-Type","")
    except HTTPError as e:
        body=e.read(64*1024);status=e.code;final=e.geturl();ctype=e.headers.get("Content-Type","")
    except (URLError,TimeoutError) as e:
        return {"canonical_url":url,"retrieved_at":retrieved,"status":"blocked_or_unavailable","error_class":type(e).__name__,"page_content_obtained":False,"verified":False,"limitations":"No authorization or access restriction was bypassed."}
    parser=Text()
    try:parser.feed(body.decode("utf-8",errors="replace"))
    except Exception:pass
    visible=" ".join(parser.data)
    shell="This website requires JavaScript" in visible or len(visible)<250
    content_obtained=status==200 and "text/html" in ctype.lower() and not shell
    return {"canonical_url":url,"retrieved_at":retrieved,"http_status":status,"final_url":final,"content_type":ctype,"response_bytes":len(body),"response_sha256":hashlib.sha256(body).hexdigest(),"page_title":" ".join(parser.title_text)[:200],"meta_description":parser.description[:500],"visible_non_script_text_chars":len(visible),"status":"content_retrieved" if content_obtained else "retrieved_shell" if status==200 else "blocked_or_unavailable","page_content_obtained":content_obtained,"verified":False,"human_verification_required":True,"limitations":"A successful HTTP response is not proof of page-content review. No body is stored; an actual content summary and human review record are required before VERIFIED."}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("url");p.add_argument("--output",type=Path);a=p.parse_args()
    try:
        result=fetch(a.url);out=json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)
        if a.output:a.output.write_text(out+"\n",encoding="utf-8")
        print(out);return 0 if result["status"] in {"content_retrieved","retrieved_shell"} else 2
    except (ValueError,OSError,json.JSONDecodeError) as e:print(f"BLOCKED: {e}",file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
