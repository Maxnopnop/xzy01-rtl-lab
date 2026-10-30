"""Read-only analysis of frozen experiment receipts; never calls a model."""
from pathlib import Path
import sys, json, hashlib, collections, html
sys.path.insert(0, 'C:/Users/A/.cache/xzy01-chart-deps')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SOURCE = ROOT/'validation/rag-paired240-audit-v1/all120-pairs.json'
rows = json.loads(SOURCE.read_text(encoding='utf-8'))
raw_results = ROOT/'validation/openrouter-resume198-v1/runtime/continuation/results'
font = FontProperties(fname='C:/Windows/Fonts/msyh.ttc')
plt.rcParams.update({'font.family':font.get_name(), 'axes.unicode_minus':False,
 'font.size':11, 'axes.spines.top':False, 'axes.spines.right':False,
 'figure.facecolor':'#f5f7fb', 'axes.facecolor':'#ffffff', 'savefig.facecolor':'#f5f7fb'})
MODELS=['gpt-5.6-luna','gpt-5.6-terra','gpt-5.6-sol']
SHORT=['Luna','Terra','Sol']
COLORS=['#4169be','#00a394']
GROUPS=['已确认清晰','其他候选','规格／参考冲突','语义歧义','历史近重复','结构要求冲突']
def group(task):
 if task.startswith(('Prob023_','Prob032_')): return GROUPS[0]
 if task.startswith('Prob149_'): return GROUPS[2]
 if task.startswith(('Prob089_','Prob146_','Prob064_','Prob132_')): return GROUPS[3]
 if task.startswith(('Prob029_','Prob033_','Prob071_','Prob109_','Prob150_')): return GROUPS[4]
 if task.startswith('Prob131_'): return GROUPS[5]
 return GROUPS[1]
for r in rows:
 r['display_group']=group(r['task'])
 for cond in ['no_rag','rag']:
  rid='__'.join([r['task'],cond,r['model'],r['sample']])
  receipt=json.loads((raw_results/(rid+'.json')).read_text(encoding='utf-8'))
  assert receipt['status']==r[cond]
assert len(rows)==120
assert sum(r[c]=='REFERENCE_PASS' for r in rows for c in ['no_rag','rag'])==194
def stats(rs,model,cond):
 ss=[r for r in rs if r['model']==model]
 service=sum('SERVICE' in r[cond] for r in ss)
 n=len(ss)-service
 k=sum(r[cond]=='REFERENCE_PASS' for r in ss)
 return k,n,service
def rates(ax,rs,title):
 for j,c in enumerate(['no_rag','rag']):
  ss=[stats(rs,m,c) for m in MODELS]
  x=[i+(j-.5)*.36 for i in range(3)]
  heights=[100*k/n if n else 0 for k,n,s in ss]
  bars=ax.bar(x,heights,width=.33,color=COLORS[j],label=['无 RAG','有 RAG'][j],zorder=3)
  for bar,(k,n,s) in zip(bars,ss):
   ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+2,f'{k}/{n}\n{100*k/n:.1f}%' if n else '不可评估',ha='center',va='bottom',fontsize=9)
 ax.set_xticks(range(3),SHORT);ax.set_ylim(0,126);ax.set_yticks([0,25,50,75,100]);ax.set_ylabel('参考测试通过率（%）')
 ax.set_title(title,loc='left',fontweight='bold',pad=14);ax.grid(axis='y',alpha=.18,zorder=0)

fig,axs=plt.subplots(1,2,figsize=(15,6.5));fig.subplots_adjust(top=.77,bottom=.23,wspace=.22)
fig.suptitle('240 槽实验｜有无 RAG 的全量观察',x=.06,ha='left',fontsize=23,fontweight='bold',y=.97)
fig.text(.06,.87,'20 题 × 3 模型 × 2 条件 × 2 次样本；包含有争议及历史近重复题，不能视作干净保留集。',fontsize=12,color='#4b5563')
rates(axs[0],rows,'01  三模型通过率');axs[0].legend(loc='upper left',bbox_to_anchor=(0,1.04),ncol=2,frameon=False,fontsize=10)
for j,(cat,label,color) in enumerate([('help','失败 → 通过','#00a394'),('worse','通过 → 失败','#df7351')]):
 vals=[sum(r['model']==m and r['category']==cat for r in rows) for m in MODELS]
 bars=axs[1].bar([i+(j-.5)*.36 for i in range(3)],vals,width=.33,color=color,label=label,zorder=3)
 for b,v in zip(bars,vals):axs[1].text(b.get_x()+b.get_width()/2,v+.09,str(v),ha='center',fontweight='bold',fontsize=15)
axs[1].set_xticks(range(3),SHORT);axs[1].set_ylim(0,4.5);axs[1].set_yticks(range(5));axs[1].grid(axis='y',alpha=.18)
axs[1].set_ylabel('配对案例数');axs[1].set_title('02  RAG 帮助与变差：各 5 对',loc='left',fontweight='bold',pad=14)
axs[1].legend(loc='upper left',ncol=2,frameon=False,fontsize=10)
fig.text(.06,.12,'服务失败单列：Sol 无 RAG 1 次（第 197 槽，内部 502）；有 RAG 1 次（第 83 槽，429）。',fontsize=11)
fig.text(.06,.075,'通过率分母排除服务失败，包含编译失败／RTL 被拒绝／参考测试失败。配对：91 同过、17 同未过、5 帮助、5 变差、2 不可比。',fontsize=10)
fig.text(.06,.035,'“帮助／变差”为结果差异，并非已证明因果；独立生成、每条件仅 2 次。未调用模型，未改 RAG、提示词、题目。',fontsize=10,color='#4b5563')
fig.savefig(HERE/'01_overview.png',dpi=160);fig.savefig(HERE/'01_overview.svg');plt.close(fig)

fig,axs=plt.subplots(2,3,figsize=(17,10));fig.subplots_adjust(top=.83,bottom=.16,hspace=.45,wspace=.23)
fig.suptitle('分组展示｜规格冲突、歧义与历史近重复不混算',x=.055,ha='left',fontsize=23,fontweight='bold',y=.97)
fig.text(.055,.91,'沿用实验前审阅的分类；只是展示分层，没有修改原标签、试题、参考或检索结果。',fontsize=12,color='#4b5563')
for ax,g in zip(axs.flat,GROUPS):
 rs=[r for r in rows if r['display_group']==g];nt=len({r['task'] for r in rs})
 rates(ax,rs,f'{g} · {nt} 题')
fig.legend(['无 RAG','有 RAG'],loc='upper right',bbox_to_anchor=(.94,.92),ncol=2,frameon=False)
fig.text(.055,.095,'已确认清晰的 2 题：各模型、各条件均 4/4。其他候选不等于已确认清晰保留集。',fontsize=12)
fig.text(.055,.055,'服务失败：其他候选 / Sol 无 RAG 1 次；历史近重复 / Sol 有 RAG 1 次。规格／参考冲突的 0% 不能解释为模型一定做错。',fontsize=11)
fig.text(.055,.022,'结构要求冲突：原题要求子模块，冻结外层提示只允许单模块；该组 12 槽均被拒绝，不用于判断 RAG 效果。',fontsize=10,color='#4b5563')
fig.savefig(HERE/'02_stratified_rates.png',dpi=160);fig.savefig(HERE/'02_stratified_rates.svg');plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(15,7));fig.subplots_adjust(top=.8,bottom=.2,left=.15,wspace=.35)
fig.suptitle('RAG 的结果变化来自哪些题组？',x=.06,ha='left',fontsize=23,fontweight='bold',y=.96)
palette=['#4169be','#00a394','#a076cd']
for ax,cat,title in zip(axs,['help','worse'],['失败 → 通过：5 对','通过 → 失败：5 对']):
 left=[0]*len(GROUPS)
 for m,label,color in zip(MODELS,SHORT,palette):
  vals=[sum(r['model']==m and r['category']==cat and r['display_group']==g for r in rows) for g in GROUPS]
  bars=ax.barh(range(len(GROUPS)),vals,left=left,color=color,label=label,height=.58)
  for i,v in enumerate(vals):
   if v:ax.text(left[i]+v/2,i,str(v),ha='center',va='center',color='white',fontweight='bold')
  left=[a+b for a,b in zip(left,vals)]
 ax.set_yticks(range(len(GROUPS)),GROUPS);ax.invert_yaxis();ax.set_xlim(0,4.5);ax.set_xticks(range(5));ax.set_xlabel('配对案例数');ax.set_title(title,loc='left',fontweight='bold');ax.grid(axis='x',alpha=.15)
fig.legend(SHORT,loc='upper right',bbox_to_anchor=(.94,.91),ncol=3,frameon=False)
fig.text(.06,.10,'118 对可比较，2 对服务失败剔出配对计数。清晰题 0 改善 / 0 变差；不代表两种方法普遍等效。',fontsize=12)
fig.text(.06,.055,'样本编号只是固定配对索引，不保证相同随机种子。历史题与歧义题上的变化仅作观察，不用于无污染保留集结论。',fontsize=11,color='#4b5563')
fig.savefig(HERE/'03_changes_by_group.png',dpi=160);fig.savefig(HERE/'03_changes_by_group.svg');plt.close(fig)

metrics={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'generation_calls':0,'total_slots':240,'pairs':120,'groups':{g:{m:{c:stats([r for r in rows if r['display_group']==g],m,c) for c in ['no_rag','rag']} for m in MODELS} for g in GROUPS}}
(HERE/'chart-data.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
changed=[r for r in rows if r['category'] in ['help','worse','service_unpaired']]
table=''.join('<tr>'+''.join('<td>'+html.escape(str(r[k]))+'</td>' for k in ['task','model','sample','no_rag','rag','display_group'])+'</tr>' for r in changed)
page='''<!doctype html><meta charset="utf-8"><title>XZY01 RAG 实验图表</title><style>body{font:16px/1.7 "Microsoft YaHei",sans-serif;background:#f5f7fb;color:#14243b;max-width:1400px;margin:40px auto;padding:0 24px}img{width:100%;border-radius:16px;margin:20px 0}table{border-collapse:collapse;width:100%;font-size:13px}td,th{padding:10px;border-bottom:1px solid #ccd5e1;text-align:left}a{color:#4169be}</style><h1>XZY01：有无 RAG 的 240 槽实验</h1><p>194 次参考测试通过，44 次非服务未通过，2 次服务失败；服务失败保留原记录，不补跑。下图为只读分析，不证明 RAG 因果收益。没有调用模型，也没有修改 RAG、提示词或题目。</p>'''
for name in ['01_overview','02_stratified_rates','03_changes_by_group']:page+=f'<img src="{name}.png"><p><a href="{name}.svg">下载矢量 SVG</a></p>'
page+='<h2>全部结果变化及服务失败案例</h2><table><tr><th>题目</th><th>模型</th><th>样本</th><th>无 RAG</th><th>有 RAG</th><th>题组</th></tr>'+table+'</table><p>完整题目列表：<a href="../rag-paired240-audit-v1/ALL20_COMPARISON.txt">20题逐模型对照</a>。分组依据：实验前 ALL20_REVIEW.md；Prob109 同时披露时钟边沿未明确，主标签按历史近重复展示。</p>'
(HERE/'index.html').write_text(page,encoding='utf-8')
print(json.dumps({'figures':3,'pairs':len(rows),'status':'BUILT','path':str(HERE)},ensure_ascii=False))
