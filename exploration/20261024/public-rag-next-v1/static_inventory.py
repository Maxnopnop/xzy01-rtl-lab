"""Text evidence inventory only. No HDL parser/compiler/simulator execution."""
import json,re,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
rows=[]
for t in json.loads((P/'protocol/overlay.json').read_bytes())['new_candidates']:
    task=t['id'];base=P/'B/originals/dataset_spec-to-rtl';test=(base/(task+'_test.sv')).read_text();ref=(base/(task+'_ref.sv')).read_text();prompt=(base/(task+'_prompt.txt')).read_text()
    lines=test.splitlines();excerpts=[]
    for i,l in enumerate(lines):
        if any(x in l for x in ['always @','wait_for_end_of_timestep','assign tb_match','`include','$readmem','RefModule good','TopModule top']):excerpts.append({'line':i+1,'text':l})
    stimulus=test.split('endmodule',1)[0]+'endmodule'
    modules=re.findall(r'\bmodule\s+(\w+)',test+'\n'+ref)
    row={'id':task,'modules':modules,'includes':re.findall(r'`include\s+"([^"]+)"',test+ref),'readmem':bool(re.search(r'\$readmem',test+ref)),'test_helper_name_occurrences':test.count('wait_for_end_of_timestep'),'evidence':excerpts,'stimulus':stimulus,'reference_text':ref,'prompt_interfaces':re.findall(r'^\s*-\s+(?:input|output).*$',prompt,re.M),'file_authorship':'No individual file author attribution established; upstream repository authorship only, snapshot commit author not substituted','reference_independence':'SAME_REPOSITORY_CORRELATED_NO_INDEPENDENT_ORACLE','simulation':'NOT_RUN','static_inventory_not_proof':True}
    rows.append(row)
(P/'B/static-inventory.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for r in rows:
    print(r['id'],r['modules'],'helper',r['test_helper_name_occurrences'],'includes',r['includes'],'readmem',r['readmem'])
