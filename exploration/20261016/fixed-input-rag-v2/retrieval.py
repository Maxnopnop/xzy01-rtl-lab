"""Deterministic local lexical retrieval; only stdlib, no network/model access."""
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SECTIONS={'Blocking and Non-blocking Assignments','Delay Modeling',
          'Sequential Logic (Latches)','Sequential Logic (Registers)',
          'Combinational Logic','Case Statements'}
STOP=set('a an the and or of to in for with on as is are be by from this that it its use using only each at after before when then do not must should'.split())
TASKS=['rt_sequence','sticky_alarm','event_parity','request_delay','debounce3']
def digest(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(name,obj):
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
def terms(s):return [x for x in re.findall(r'[a-z][a-z0-9_]*',s.lower()) if x not in STOP]
def build_corpus():
    lines=(HERE/'upstream/VerilogCodingStyle.md').read_text(encoding='utf-8').splitlines()
    chunks=[];excluded=[];section='';fenced=False;paragraph=[]
    def flush():
        nonlocal paragraph
        if not paragraph:return
        body='\n'.join(s for _,s in paragraph)
        start,end=paragraph[0][0],paragraph[-1][0]
        reason=None
        if not 80<=len(body)<=900:reason='length_outside_80_900'
        elif re.search(r'http|\]\(|&#|^\s*\||example|e\.g\.|below|shown|following|cond[12]|foo_|\babc\b|0xAB',body,re.I):reason='external_link_or_code_example_dependency'
        elif any(t in body.lower() for t in TASKS+['1001','sequence_detector']):reason='task_specific_marker'
        elif len(chunks)>=40:reason='fixed_40_chunk_cap'
        if reason:excluded.append(dict(start_line=start,end_line=end,reason=reason,sha256=digest(body.encode())))
        else:
            chunks.append(dict(id=f'LR{len(chunks)+1:03d}',section=section,start_line=start,
                end_line=end,text=body,sha256=digest(body.encode()),characters=len(body),
                use='General synthesizable language/style guidance, not task requirements or a solution'))
        paragraph=[]
    for number,line in enumerate(lines,1):
        if line.strip().startswith('```'):
            flush();fenced=not fenced;continue
        if fenced:continue
        heading=re.match(r'^(#{1,3})\s+(.*)',line)
        if heading:
            flush();section=heading[2] if len(heading[1])==3 else '';continue
        if section not in SECTIONS:continue
        if not line.strip():flush()
        else:paragraph.append((number,line))
    flush()
    assert 0<len(chunks)<=40
    return chunks,excluded
def retrieve(query,chunks):
    bags=[Counter(terms(c['section']+'\n'+c['text'])) for c in chunks]
    lengths=[sum(b.values()) for b in bags];avg=sum(lengths)/len(lengths)
    qterms=sorted(set(terms(query)));rows=[]
    for c,bag,dl in zip(chunks,bags,lengths):
        score=0.;matched=[]
        for token in qterms:
            tf=bag[token]
            if not tf:continue
            df=sum(token in b for b in bags)
            idf=math.log(1+(len(chunks)-df+0.5)/(df+0.5))
            contribution=idf*(tf*2.2)/(tf+1.2*(1-0.75+0.75*dl/avg))
            score+=contribution;matched.append({'term':token,'tf':tf,'df':df,'contribution':contribution})
        rows.append(dict(chunk_id=c['id'],score=score,matched=matched))
    ranked=sorted(rows,key=lambda r:(-r['score'],r['chunk_id']))
    selected=[r for r in ranked if r['score']>0][:3]
    return dict(query=query,query_sha256=digest(query.encode()),query_terms=qterms,
                rankings=ranked,selected_ids=[r['chunk_id'] for r in selected],no_hit=not selected)
def main():
    assert not (HERE/'corpus-lock.json').exists(),'Corpus already frozen; do not overwrite'
    chunks,excluded=build_corpus()
    write('corpus/chunks.json',chunks);write('corpus/exclusions.json',excluded)
    info=read(HERE/'upstream/commit.json');rev=info['sha']
    access=read(HERE/'access.json')
    license_text=(HERE/'upstream/LICENSE').read_text(encoding='utf-8')
    assert 'Attribution 4.0 International' in license_text
    write('corpus/manifest.json',dict(source_count=1,chunk_count=len(chunks),
        source={'title':'lowRISC Verilog Coding Style Guide','attribution':'lowRISC contributors',
          'repository':'https://github.com/lowRISC/style-guides','commit':rev,
          'document_url':f'https://github.com/lowRISC/style-guides/blob/{rev}/VerilogCodingStyle.md',
          'license':'CC-BY-4.0','license_url':'https://creativecommons.org/licenses/by/4.0/',
          'original_sha256':digest((HERE/'upstream/VerilogCodingStyle.md').read_bytes()),
          'license_sha256':digest((HERE/'upstream/LICENSE').read_bytes()),
          'retrieved_utc':next(r['utc'] for r in access if r['path'].endswith('VerilogCodingStyle.md'))},
        changes='Selected prose paragraphs, no text rewriting; headings/provenance are contextual metadata. Full original and license retained.',
        authority='Project style guidance, not normative SystemVerilog LRM. Its conventions cannot override original task.',
        development_exposure=True,training_contamination='UNKNOWN'))
    specs={s['id']:s for s in read(ROOT/'benchmarks/paired-v1/manifest.json')['tasks']}
    for task in TASKS:
        result=retrieve(specs[task]['spec'],chunks)
        result['selected_chunks']=[next(c for c in chunks if c['id']==i) for i in result['selected_ids']]
        write('retrieval/'+task+'.json',result)
    write('corpus-lock.json',{p.relative_to(HERE).as_posix():digest(p.read_bytes())
        for folder in ('upstream','corpus','retrieval') for p in sorted((HERE/folder).rglob('*')) if p.is_file()})
    print(json.dumps({'chunks':len(chunks),'excluded_paragraphs':len(excluded),
         'retrievals':{t:read(HERE/f'retrieval/{t}.json')['selected_ids'] for t in TASKS}}))
if __name__=='__main__':main()
