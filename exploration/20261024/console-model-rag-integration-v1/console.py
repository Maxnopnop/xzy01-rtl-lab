"""Same console UI and dispatch, versioned integration entry; no automatic calls."""
import argparse
import getpass
import json
from pathlib import Path
import sys
from tkinter import filedialog
from integration import b, gui, Package, HERE
import home_transfer as home

def export_launcher(manifest,release,destination):
    pkg=Package(manifest);release=Path(release).resolve()
    def q(s):return "'"+str(s).replace("'","''")+"'"
    python=Path(sys.executable)
    if python.name.lower()=='pythonw.exe':python=python.with_name('python.exe')
    args=[HERE/'console.py','--manifest',pkg.path,'--release',release,'--manifest-sha',pkg.identity,'--release-sha',b.sha(release),'--run-one']
    with Path(destination).open('x',encoding='utf-8') as f:
        f.write("$ErrorActionPreference = 'Stop'\n# One slot only; getpass; no key in file.\n& "+q(python)+' -B '+' '.join(q(x) for x in args)+'\nexit $LASTEXITCODE\n')

class Console(gui.Console):
    def __init__(self,root):
        super().__init__(root)
        root.title('XZY01 控制台 · 较早模型接入 v1（未放行）')
    def launcher(self):
        b.require(self.package is not None and self.release is not None,'需冻结包与放行文件')
        p=filedialog.asksaveasfilename(initialfile='Start-Model-RAG-One.ps1',defaultextension='.ps1')
        if p:export_launcher(self.package.path,self.release,p)
    def report(self):
        import uuid
        result=paired_summary(self.rows)
        path=b.STATE/('paired-report-'+uuid.uuid4().hex[:12]+'.json')
        b.save(path,result)
        self.show(self.detail,dict(result,evidence=str(path)))
    def pack(self):
        self.school_record=None
        super().pack()
        if self.school_record and 'home_sha256' not in self.school_record:
            self.school_record=home.prepare(self.school_record)
            self.show(self.schooltext,dict(self.school_record,note='仅打包；先复制 check 命令暂存到 HOME，再手动 run 一个工具。'))
    def copy_command(self,action='run'):
        b.require(self.school_record is not None and 'home_sha256' in self.school_record,'先载入新版 HOME record 或打包')
        command=home.command(self.school_record,action)
        self.root.clipboard_clear();self.root.clipboard_append(command)
        self.show(self.schooltext,{'manual_command':command,'action':action,'school_calls':0})
    def collect(self):
        if self.school_record is None:
            self.load_school_record()
            if self.school_record is None:return
        p=filedialog.askopenfilename(title='选择平铺 return-console-*.json（同目录须有同名 .zip）')
        if p:self.show(self.schooltext,home.collect_flat(self.school_record,p))

def paired_summary(rows):
    """Descriptive only: never treat transport failures as function failures."""
    by={};pairs={}
    valid={'FIXED_TEST_PASS','FUNCTION_FAIL','COMPILE_ERROR'}
    for r in rows:
        key=(r['dataset'],r['model']);g=by.setdefault(key,{a:{'opportunities':0,'fixed_test_pass':0,'rtl_evaluated':0,'statuses':{}} for a in ('no_rag','rag')})
        arm=g[r['condition']];arm['opportunities']+=1
        stage=r.get('fixed_test','NOT_RUN');arm['fixed_test_pass']+=int(stage=='FIXED_TEST_PASS');arm['rtl_evaluated']+=int(stage in valid)
        label=r.get('status','UNKNOWN')+' / '+stage;arm['statuses'][label]=arm['statuses'].get(label,0)+1
        k=(r['dataset'],r['model'],r['task'],r['sample']);pair=pairs.setdefault(k,{})
        b.require(r['condition'] not in pair,'报告出现重复条件');pair[r['condition']]=stage
    output=[]
    for (dataset,model),g in by.items():
        counts=dict(both_pass=0,both_nonpass=0,rag_help=0,rag_harm=0,unpaired_or_unevaluated=0)
        for k,pair in pairs.items():
            if k[:2]!=(dataset,model):continue
            if set(pair)!={'no_rag','rag'} or any(s not in valid for s in pair.values()):counts['unpaired_or_unevaluated']+=1;continue
            a=pair['no_rag']=='FIXED_TEST_PASS';c=pair['rag']=='FIXED_TEST_PASS'
            label='both_pass' if a and c else 'rag_help' if c else 'rag_harm' if a else 'both_nonpass';counts[label]+=1
        rates={a:(v['fixed_test_pass']/v['opportunities'] if v['opportunities'] else None) for a,v in g.items()}
        output.append(dict(dataset=dataset,model=model,arms=g,paired=counts,delta_all_opportunities=(rates['rag']-rates['no_rag']) if all(v is not None for v in rates.values()) else None))
    return dict(stage='DESCRIPTIVE_FIXED_TEST_ONLY',groups=output,note='机会分母包括未执行与服务失败；不能视为纯RTL准确率。CHECK_COUNT_DIFFERENT单列，不升级PASS。综合/门级/签核不由本表推导。20题重复及相关题组的统计分析另行冻结。')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest');parser.add_argument('--release')
    parser.add_argument('--manifest-sha');parser.add_argument('--release-sha')
    parser.add_argument('--run-one',action='store_true');parser.add_argument('--preview',action='store_true')
    args=parser.parse_args()
    if not (args.run_one or args.preview):
        root=gui.tk.Tk();Console(root);root.mainloop();return
    pkg=Package(args.manifest)
    if args.manifest_sha:b.require(pkg.identity==args.manifest_sha,'清单变化')
    if args.release_sha:b.require(b.sha(args.release)==args.release_sha,'放行文件变化')
    if args.preview:
        print(json.dumps({'rows':pkg.rows(),'model_calls':0},ensure_ascii=False,indent=2));return
    pending=[r for r in pkg.rows() if r['status']=='NOT_STARTED']
    b.require(pending,'没有未预约槽')
    slot=pending[0]['id'];pkg.gate(args.release,slot)
    if input('One paid POST for '+slot+'. Type RUN: ')!='RUN':return
    secret=getpass.getpass('OpenRouter key (hidden, process only): ')
    try:result=pkg.dispatch(args.release,slot,secret)
    finally:secret=''
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
