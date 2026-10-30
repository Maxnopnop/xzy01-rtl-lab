from pathlib import Path
import json, csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

OUT=Path(__file__).resolve().parent
plt.rcParams.update({'font.family':'Microsoft YaHei','axes.unicode_minus':False,'font.size':12,'axes.spines.top':False,'axes.spines.right':False})
studies=[
 ('基础 Pilot', [('sol',24,30),('terra',24,30)], '两个模型，各 30 份 RTL'),
 ('FSM 表达方式', [('普通文字',7,8),('状态表',7,8),('带检查状态表',8,8)], '仅两个开发题；未触发 IR 修复'),
 ('R2 · 反馈与重新生成', [('重新生成',10,10),('执行反馈',9,10)], '条件修复；含人工错误起点'),
 ('R3 · 新题族', [('重新生成',8,8),('执行反馈',8,8)], '四个开发题族；首次结果也全部通过'),
 ('R4 · 两种 IR 表达', [('JSON\n再生成',6,6),('JSON\n反馈',6,6),('线性 IR\n再生成',6,6),('线性 IR\n反馈',6,6)], '两种表达都有 IR，不是有／无 IR 对照'),
 ('R6 · 显式 IR 与直接 RTL', [('显式 IR\n再生成',6,6),('显式 IR\n反馈',6,6),('直接 RTL\n再生成',6,6),('直接 RTL\n反馈',6,6)], '三个开发题族；各最终组 6 个样本')]
feedback=[('早期固定错误 IR',5,0,42,1),('R2',0,1,9,0),('R3',0,0,8,0),('R4',0,0,12,0),('R5 · 中断',0,0,4,8),('R6',0,0,12,0)]
data={'as_of':'2026-10-16','rates':studies,'paired_feedback':feedback,'sources':['FYP_STATUS_AUDIT_20261009.md','FYP_EXPLORATION_INDEX.md','exploration/20261011/R2_RESULTS.md','exploration/20261011/r3/RESULTS.md','exploration/20261011/r4/RESULTS.md','exploration/20261011/r5/RESULTS.md','exploration/20261011/r6/execution-v2/RESULTS.md'],'notes':['Descriptive within-study comparisons only; repeated samples are not independent task families.','R5 omitted from rate chart: 2 completed final outcomes per arm / 6 planned; remaining are not failures.','Early paired trial excluded from rate chart because infrastructure-incomplete pair has arm-specific denominators.','Calls matched where specified, not strict token or cost matching.','Help/harm are paired binary pass-status differences, not within-output before/after repair rates.']}
(OUT/'chart-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'pass-rates.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['study','method','pass','denominator','percent'])
 for title,arms,note in studies:
  for name,p,n in arms:w.writerow([title,name.replace('\n',' '),p,n,100*p/n])
with (OUT/'feedback.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['study','help','harm','no_change','inconclusive','total_pairs'])
 for row in feedback:w.writerow([*row,sum(row[1:])])
fig,axes=plt.subplots(2,3,figsize=(16,10))
fig.patch.set_facecolor('#f5f7fb')
fig.suptitle('各方法功能通过率',fontsize=25,fontweight='bold',x=.055,ha='left',y=.98)
fig.text(.055,.925,'标签显示通过数／完整分母；仅比较同一面板内的方法。不同轮次题目与判据不同。',color='#475569',fontsize=13)
for ax,(title,arms,note) in zip(axes.flat,studies):
 vals=[100*p/n for _,p,n in arms];colors=['#0f766e' if '反馈' in name or '检查' in name else '#3869b1' for name,_,_ in arms]
 bars=ax.bar(range(len(arms)),vals,color=colors,width=.58)
 ax.set_ylim(0,116);ax.set_yticks([0,25,50,75,100],['0%','25%','50%','75%','100%']);ax.set_axisbelow(True);ax.grid(axis='y',alpha=.15)
 ax.set_xticks(range(len(arms)),[x[0] for x in arms],fontsize=11)
 ax.set_title(title,loc='left',fontsize=16,pad=16,fontweight='bold')
 for bar,(_,p,n),v in zip(bars,arms,vals):ax.text(bar.get_x()+bar.get_width()/2,v+2,f'{p}/{n}\n{v:g}%',ha='center',va='bottom',fontsize=11,fontweight='bold')
 ax.text(0,-.24,note,transform=ax.transAxes,color='#475569',fontsize=10)
fig.subplots_adjust(left=.055,right=.985,top=.84,bottom=.16,wspace=.24,hspace=.57)
fig.text(.055,.045,'R5 中断：各最终组仅完成 2/6，未完成项不能算失败，因此不画完整通过率。\n所有百分比均为已规定测试内的观测结果；小型开发集的 100% 不代表普遍正确或方法等效。',fontsize=11,color='#475569',linespacing=1.8)
for ext in ['png','svg']:fig.savefig(OUT/f'pass-rates.{ext}',dpi=160,facecolor=fig.get_facecolor())
plt.close(fig)
fig,ax=plt.subplots(figsize=(15,8.5));fig.patch.set_facecolor('#f5f7fb')
fig.suptitle('反馈带来的帮助与变差',fontsize=25,fontweight='bold',x=.07,ha='left',y=.97)
fig.text(.07,.91,'每行是一轮实验的配对结果；条形长度为占比，数字为配对数量。',fontsize=13,color='#475569')
colors=['#15803d','#dc2626','#cbd5e1','#e6ad36'];names=['帮助','变差','无变化','无法判断']
for i,row in enumerate(feedback):
 total=sum(row[1:]);left=0
 for j,count in enumerate(row[1:]):
  width=count/total*100
  ax.barh(i,width,left=left,color=colors[j],height=.55,label=names[j] if i==0 else None)
  if count:ax.text(left+width/2,i,str(count),va='center',ha='center',fontsize=12,fontweight='bold',color='white' if j<2 else '#172033')
  left+=width
 ax.text(102,i,f'n={total}   帮助 {row[1]} / 变差 {row[2]}',va='center',fontsize=11,color='#334155')
ax.set_yticks(range(len(feedback)),[r[0] for r in feedback]);ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xticks([0,25,50,75,100],['0%','25%','50%','75%','100%']);ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0,pad=12)
ax.legend(loc='upper left',bbox_to_anchor=(0,1.15),ncol=4,frameon=False)
fig.subplots_adjust(left=.19,right=.74,top=.77,bottom=.28)
fig.text(.07,.06,'帮助 = 反馈通过、对照失败；变差 = 反馈失败、对照通过；无变化 = 两侧通过状态相同。\n早期 5 个帮助对：2 对重复同一自然错误，3 对来自人工错误；对照策略与后续轮次不同。\nR5 有 8 对无法判断，保留在完整分母；各轮不可合并为总体因果效应或独立题族成功率。',fontsize=11,color='#475569',linespacing=1.9)
for ext in ['png','svg']:fig.savefig(OUT/f'feedback-effects.{ext}',dpi=160,facecolor=fig.get_facecolor())
plt.close(fig)
print(OUT)
