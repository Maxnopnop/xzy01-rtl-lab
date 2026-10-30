"""Human static review transcription; never executes RTL or retrieval."""
import json,hashlib,datetime,re
from pathlib import Path
P=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
    assert not p.exists(),p;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
# eligible, title, decision, contract, history, original stimulus coverage
reviews={
'Prob145_circuit8':(False,'波形推断锁存器及下降沿寄存器','KEY_TIMING_UNRESOLVED','clock/a/p/q均1位；无复位、初态X。表中115ns时clock下降且a变0，而q变1；没有区分边沿前/后输入。参考q<=a、p高电平透明，不足以唯一解释原表同时变化。','与dff历史有局部相似，决定性排除是原波形采样相位无法唯一确定。','子clock每3个posedge测试clk翻转，a在测试双边沿NBA更新；200随机步。不能以参考一致倒推出唯一契约。'),
'Prob088_ece241_2014_q5b':(False,'串行二补数Mealy FSM','REFERENCE_STRUCTURE_CONFLICT','全1位，posedge、异步高复位A，A遇1转B，z由state/x决定。原题要求one-hot，参考reg state为单比特二进制A=0/B=1，不满足两状态one-hot结构。','与旧Prob089二补数题同族；不靠实现编码差异宣称新独立题。','异步reset_test及400随机双边沿输入；TB只看z，不检查one-hot编码。'),
'Prob122_kmap4':(False,'四输入卡诺图奇偶','HISTORY_FUNCTIONAL_NEAR_DUPLICATE','1位a,b,c,d/out；完整Gray顺序16格；组合、无时钟复位、无符号运算；函数为四位奇偶。','与历史parity8功能相同，仅宽度/表达形式改变；不是新独立奇偶测试。','16枚举+200随机，参考case无default导致X输入未覆盖定义；不修改。'),
'Prob001_zero':(True,'常零输出','CONDITIONAL_STATIC_ELIGIBLE','仅1位zero，无输入、时钟、复位、有符号算术；始终为0，组合连续有效，不涉及初始化契约。','未见相同常零任务；与NOT/门运算共有常量这一基本原语不单独判重复。','20个测试时钟双边沿观测，无输入空间；同源参考assign0，非独立oracle。'),
'Prob155_lemmings4':(False,'行走坠落挖掘死亡FSM','HISTORY_SUBSTANTIVE_OVERLAP','全1位接口，posedge、异步高复位walk_left；fall优先dig优先转向；落地且下落超过20周期死亡，初态靠reset。','旧Prob127_lemmings1同一Lemmings左右行走/碰撞状态核心，且历史计数/状态扩展已暴露；保守排除，不把加dig/dead当全新独立题。','含20/21/24/35/67周期坠落、reset及随机；参考fall_counter独立时序过程无异步复位，其精确边界未作独立验证。'),
'Prob019_m2014_q4f':(True,'带反相输入的AND','CONDITIONAL_STATIC_ELIGIBLE','in1/in2/out均1位，组合out=in1 AND NOT in2，无时钟复位或符号问题；文字完整描述bubble，无缺图。','旧Prob029是XNOR再XOR，旧Prob065是双四输入NAND；共有门原语但不是同一完整函数。与本批Prob087有共享输出，统计须标相关题组。','100双边沿随机输入，非预声明穷举；评分看已稳定旧输入阶段，无统一postsettle保证。'),
'Prob151_review2015_fsm':(False,'1101触发四周期移位计时控制','HISTORY_FUNCTIONAL_NEAR_DUPLICATE','posedge同步高复位；检测1101后shift_ena4周期，再counting等done_counting，done等ack；完整timer控制。','旧Prob150_review2015_fsmonehot给出同一10状态图，另Prob095/096相关题已暴露；相同控制行为的组合/寄存器包装变化不成为独立新题。','5000随机双边沿及示例序列；参考enum cast依赖SystemVerilog工具支持，本轮不编译。'),
'Prob094_gatesv':(True,'相邻位关系与环绕差异','CONDITIONAL_STATIC_ELIGIBLE','in及三output均4位；out_both[2:0]相邻AND；out_any[3:1]相邻OR；out_different含3到0环绕XOR。out_both[3]/out_any[0]原题明确不关心；组合、无时钟复位、有符号运算。','旧vectorgates直接对两输入向量做OR/NOT，无本题相邻索引与环绕关系；共享门原语，不是仅改位宽。','定向3/6/12/9/5加双边沿随机；参考将两无效边界位设X，TB屏蔽这些位，不能声称所有12位均受约束。'),
'Prob143_fsm_onehot':(True,'十状态组合转移逻辑','CONDITIONAL_STATIC_ELIGIBLE','state[9:0]、next_state[9:0]及1位in/out1/out2；仅组合不含状态寄存器。完整图逐入边形成各next位，多有效state允许并存；输出按指定活跃状态并集，无时钟复位初态。','旧Prob150虽也10状态one-hot，但图为1101计时器，本题为连续1长度分支图，端口/转移/输出行为实质不同；FSM表达原语共享单列。','原TB先遍历10状态×2输入，再200随机one-hot；未覆盖题中允许的多hot组合，0态阶段in未初始化。多hot正确性待独立验证，不能以原TB通过证明。'),
'Prob059_wire4':(False,'三输入四输出连线','HISTORY_SUBSTANTIVE_OVERLAP','a,b,c与w,x,y,z均1位，w=a,x=b,y=b,z=c；无时钟复位，连续有效。','旧Prob032_vector0已为3位输入复制并拆到输出，本题仅改端口分组及复制次数，主要行为都是三输入无计算布线/扇出；保守近重复排除。','108个左右测试周期随机双边沿驱动，参考concat直接连线。'),
'Prob006_vectorr':(False,'八位反转','HISTORY_FUNCTIONAL_NEAR_DUPLICATE','in/out8位，无符号组合out[i]=in[7-i]，无时钟复位。','旧Prob023_vector100r相同位序反转，仅100改8位，排除。','定向位模式+200随机，参考显式反序拼接。'),
'Prob052_gates100':(False,'百位AND/OR/XOR规约','HISTORY_SUBSTANTIVE_OVERLAP','in100位，三个1位输出规约AND/OR/XOR，组合无复位时钟。','XOR规约与历史parity8宽度变体，OR规约与旧向量逻辑OR重叠；多输出打包未足以消除主体功能暴露，保守排除。','定向全0/全1/单bit/反单bit及随机；随机32位扩展不等于均匀100位空间，原样保留。'),
'Prob111_fsm2s':(False,'两状态JK式Moore FSM','CLOCK_EDGE_UNSPECIFIED','clk/reset/j/k/out均1位；同步高复位OFF与状态图明确，但原文未指定有效时钟边沿；参考选择posedge，不能用参考补原题。','与历史两状态FSM有原语共享；排除依据是关键边沿缺失，不是预期模型难度。','reset_test及200随机双边沿；TB依赖参考posedge，未提供独立契约。'),
'Prob114_bugs_case':(True,'数字键扫描码映射','CONDITIONAL_STATIC_ELIGIBLE','code8位,out4位,valid1位；十个明确常量映射0..9，其他out=0且valid=0；纯组合全时有效，unsigned字面值，无时钟复位。','历史decoder3为索引one-hot译码，本题为稀疏非连续scancode到数字映射，非宽度或重命名变体；与本批箭头scancode为相关表驱动题组。','列举十码及若干无效码+1000随机，非保证全256遍历；参考default valid0/out预置0，没有latch。'),
'Prob084_ece241_2013_q12':(False,'移位写入随机读LUT','HISTORY_SUBSTANTIVE_OVERLAP','posedge同步enable；8位移位S入Q0，Z=Q[ABC]，无reset、未定义初始存储；有效内容需移入。','历史shiftreg8/rt_shift与mux8已有移位及索引选择主体组合，保守排除；不因加存储名义重标独立。','先写8bit构造AND，再500随机；写满前参考X由TB掩蔽，结构ONLY移位器和mux未独立检查。'),
'Prob087_gates':(True,'七种二输入逻辑门','CONDITIONAL_STATIC_ELIGIBLE','a,b及七outputs1位；AND/OR/XOR/NAND/NOR/XNOR/a&~b全部指定，组合连续有效，无符号/时钟/复位。','共享旧门原语但七函数接口未发现完整历史同题；与本批Prob019共享一个输出，须报告相关性，不能当完全独立题族。','列举00/01/10/11后200随机；参考各连续assign；初始未驱动阶段可X屏蔽。'),
'Prob050_kmap1':(True,'三输入卡诺图','CONDITIONAL_STATIC_ELIGIBLE','a,b,c/out均1位，完整8格图，除000外输出1；组合无时钟复位，输出连续有效，未声明4态输入真值。','与旧多输出向量门共有OR基本原语；本题完整单输出真值表不同，无同题宽度替换证据。后续Prob101属同轮OR近重复，后者排除。','10递增输入覆盖3位0..7并回绕，加200随机；参考a|b|c。'),
'Prob101_circuit4':(False,'波形推断二输入OR','WITHIN_ROUND_FUNCTIONAL_NEAR_DUPLICATE','a,b,c,d/q均1位；表覆盖16个二值组合，q=b|c，a/d无关；组合无时钟复位。','与本轮更早Prob050同为OR归约真值表，仅有效输入数/表示变化，保守排除后者；没有依据RAG表现选留。','枚举18步覆盖16组合及100随机；波形本身完整，排除非缺图。'),
'Prob106_always_nolatches':(True,'箭头扫描码识别','CONDITIONAL_STATIC_ELIGIBLE','scancode16位，四1位方向输出；e06b/e072/e074/e075分别置对应位，其他全0；组合无时钟复位、全时有效。','与历史一般decoder只有表查找原语共享；本轮Prob114为数字输出稀疏表，本题为方向one-hot输出，保留相关表驱动题组标记，不声称完全独立族。','定向有效/相邻无效码与30000随机；不等于穷尽65536，参考每次输出全0再case。'),
'Prob154_fsm_ps2data':(False,'三字节包边界与输出','KEY_TIMING_UNRESOLVED','posedge同步reset；in8/out24/done1，first byte in[3]=1，done有效时三字节高到低。文字说第三字节后立即一周期，表在15/25/35边沿列2c/81/09却45才done；未定义表输入在边沿前还是后，参考按已采样输入转DONE。','与历史serial/framed任务有重叠，决定性排除为表/文字的采样约定未定，不能补题。','初200次negedge随机reset/data，随后三字节序列；不强制初始reset，ref out_bytes在done外X，TB掩蔽，不能据此证明数据窗口外定义。')}
cfg=read(P/'protocol/overlay.json');access=read(P/'B/access.json');inventory=read(P/'B/static-inventory.json');rows=[]
for c in cfg['new_candidates']:
    i=c['id'];ok,title,code,contract,history,coverage=reviews[i]
    inv=next(v for v in inventory if v['id']==i);assert inv['test_helper_name_occurrences']==1 and not inv['includes'] and not inv['readmem']
    bindings={r['kind']:{k:r[k] for k in ['local','url','sha256','expected_git_blob','actual_git_blob']} for r in access if r['task']==i}
    ref=(P/bindings['ref.sv']['local']).read_text();test=(P/bindings['test.sv']['local']).read_text()
    clean=lambda s:re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
    modules=re.findall(r'\bmodule\s+(\w+)',clean(ref+'\n'+test))
    assert sorted(modules)==['RefModule','stimulus_gen','tb']
    assert re.search(r'\bTopModule\s+top_module1\s*\(',test)
    rows.append({'rank':c['rank'],'id':i,'meaning_zh':title,'eligible':ok,'selected':False,'status':'CONDITIONAL_NO_INDEPENDENT_ORACLE' if ok else 'EXCLUDED','code':code,'contract_zh':contract,'history_review_zh':history,'coverage_zh':coverage,'language':'English prompt; SystemVerilog reference/TB, fixed TopModule candidate interface','diagram_or_table':'Any required textual table/diagram reviewed above; never supplemented','signedness':'No signed arithmetic requirement; widths as original interface; four-state unspecified domains not filled','initialization_and_validity':'See per-task contract; no new initialization/reset/output masking added','sampling_zh':'原test计分always位于测试clk双边沿，helper只定义未调用；NBA驱动与active区比较，不保证统一POST/NBA后采样。组合稳定输入阶段比较不等于全时序签核。','dependencies':{'modules':modules,'external_include':[],'readmem':False,'source_files':['prompt.txt','ref.sv','test.sv'],'single_topmodule':'Original TB instantiates TopModule; reference header independently present; static compatible, compile NOT_RUN'},'authorship':{'repository':'NVlabs/verilog-eval','license':'MIT (frozen LICENSE)','snapshot_commit_author':'Nathaniel Pinckney; NOT attributed as individual file author','individual_prompt_ref_test_authors':'UNKNOWN from available files; same repository lineage, no independently authored oracle established'},'reference_independence':'SAME_REPOSITORY_CORRELATED','independent_correctness':'NOT_ESTABLISHED','test_evidence':inv['evidence'],'bindings':bindings})
selected=[r['id'] for r in rows if r['eligible']][:12]
for r in rows:r['selected']=r['id'] in selected
put(P/'B/selection.json',{'utc':utc(),'a_lock_sha256':sha(P/'A-lock.json'),'protocol_lock_sha256':sha(P/'protocol-lock.json'),'candidate_count':len(rows),'selected_ids':selected,'conditional_count':len(selected),'independent_pass_count':0,'rows':rows,'selection_uses_retrieval':False,'new_model_or_eda_calls':0})
put(P/'B-lock.json',{p.relative_to(P/'B').as_posix():sha(p) for p in sorted((P/'B').rglob('*')) if p.is_file()})
put(P/'B-seal.json',{'frozen_utc':utc(),'b_lock_sha256':sha(P/'B-lock.json'),'a_lock_sha256':sha(P/'A-lock.json'),'protocol_lock_sha256':sha(P/'protocol-lock.json'),'selected_ids':selected,'retrieval_calls_so_far':0})
print(json.dumps({'selected':selected,'conditional':len(selected),'excluded':len(rows)-len(selected),'planned_slots':12*len(selected)}))
