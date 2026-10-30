"""Record static human-readable review; no simulator, retrieval, or model execution."""
import hashlib,json,re
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Rank-keyed notes correspond to immutable scope, never reordered by retrieval or score.
notes={
1:('MAIN_CANDIDATE','四个8位无符号数取最小值','ref先min=a，再依次与b/c/d比较并替换；循环不变式为已访问元素最小值，最终覆盖四项。相等返回相同数值；0/255边界无需特殊处理，无时钟/reset。','比较器原语相关，但不是原二输入比较标志功能；保留旧条件纳入及已读标签。','MIN4','原TB五组定向最小位置及100随机边沿，未声明穷举32位输入。'),
2:('AUXILIARY','行走/坠落记方向四状态Moore机','1位控制，2位state；posedge clk，posedge areset异步优先WL。WL/WR先判断ground，故落地/离地与bump同周期均不改方向；FALL状态忽略bump。双bump按当前方向翻转，符合文字。非法state缺default，非复位前有效契约。','保留Prob127/155行走坠落实质重叠。','LEMMINGS','原TB含异步reset_test、定向坠落及400次随机，不能证明所有半周期变化均覆盖。'),
3:('MAIN_CANDIDATE','512位Rule110元胞自动机','posedge、load优先、无reset；ref为NOT(111或000或100)，逐三元组与原8行真值相符。左邻q[511:1]在512位按位表达式零扩展，右邻拼0，边界为0。初态未加载前不约束。','保留旧条件纳入；与108同接口/加载/边界结构相关，不把两题作独立族。','CELLULAR_512','原TB加载bit0、bit256、4df、随机及连续load后演化；$random只有32位来源，非512位均匀覆盖。'),
4:('AUXILIARY','4位加法含第5位进位','x/y unsigned4，5位上下文加法保留最大15+15=30。无时钟/reset。ref用加号而非显式全加器；功能TB不能验证必须full adders的结构要求。','保留adder8/加减器宽度变体标签。','ADDER','原TB100随机，不保证穷举256对。'),
5:('DO_NOT_EXECUTE','六状态机的y[1]下一状态组合逻辑','ref case({y,w})覆盖12个合法组合，与转移图下一状态bit1一致；非法110/111返回X。原文同时说next-state和output Y1 is y[1]。例如y=001,w=0，下一C=010应1，而当前y[1]=0，存在可见冲突。无clk接口。','保留原关键契约歧义；与138反相输入图同构。','FSM6_COMPLEMENT','原TB随机含非法state，参考X屏蔽比较，不修正文案。'),
6:('AUXILIARY','assign和always两路AND','两输出均a&b，1位组合全赋值；无reset、多hot含a=b=1输出1。语法结构仅静态ref满足，功能TB不能检查模型用了哪种语法。','保留历史087 AND重复；与本轮090同AND功能。','AND','原TB计数遍历及200随机边沿。'),
7:('AUXILIARY','101后两周期检查y并锁定输出','同步低有效resetn优先A；A->B输出f一周期，后S0/S1/S10检测101；G1/G2窗口y成功进入P1否则P0，永久状态直到reset。S1遇1保持，允许前缀重叠。','保留历史sequence101实质重叠及扩展控制的保守标签。','SEQ101','原TB随机reset/x/y；起始resetn在posedge用阻塞释放存在与state采样竞态。'),
8:('AUXILIARY','两个2位数相等比较','unsigned2等号输出1位；16组合中仅00/00、01/01、10/10、11/11为1，无reset。X输入未规定。','保留历史rt_comparator等值支路宽度变体。','EQUALITY','原TB1000negedge期间随机取4位，非正式全覆盖证明。'),
9:('AUXILIARY','4位低位优先编码','2位pos；0=>0，非零取最低置1下标，ref显式16行均符合；多hot如1010=>1，与例子强调最低位一致。无reset。','保留encoder4优先方向变体旧标签。','PRIORITY_ENCODER','原TB一热移位、16值递增及随机。'),
10:('AUXILIARY','z=(x xor y) and x','布尔化简x & ~y，四行00/01/10/11输出0/0/1/0；ref与题逐字公式相同。无reset。','保留019和087 out_anotb同功能。','AND_NOT','原TB随机四组合。'),
11:('AUXILIARY','512位Rule90元胞自动机','posedge load优先；q_next[i]=q[i+1] xor q[i-1]，左511位零扩展、右拼0；两端虚拟邻居0。无reset，load前初值未规定。','保留124轮内结构相关，局部规则不同不洗掉标签。','CELLULAR_512','加载边界/中间单bit及长演化，未穷举512位状态。'),
12:('AUXILIARY','HDLC连续1计数及丢弃/flag/error','同步高reset最后NBA赋S0覆盖转移；5个1后0进SDISC、6后0进SFLAG、7后1进SERR并保持至0，输出Moore完整周期。非法state给X。','保留143同十状态转移图的历史暴露。','HDLC','原TB800随机偏向1并随机reset，特定长串覆盖不由次数保证。'),
13:('AUXILIARY','起始0、8数据、停止1的串行done','同步高reset到START；start检测后B0..B7八拍，STOP检查，DONE一拍且可立即收下个start；ERR等1后重启。1位流，无输出载荷。','保留146串行数据接收控制骨架重叠。','SERIAL','原TB定向合法/错误停止与800随机；最小状态数未要求。'),
14:('AUXILIARY','Mealy重叠101检测','negedge aresetn异步低reset到S；3态S/S1/S10。S10时z=x组合，S10遇1回S1保留重叠10101。输出会在边沿间随x改变，不能用Moore保持判据。','保留sequence101同序列与139相关。','SEQ101','reset_test及定向重叠与400随机；原计分仍边沿active采样。'),
15:('DO_NOT_EXECUTE','7位历史gshare预测器','7位PC/history xor索引128x2bit，饱和计数0..3；mis-predict训练后写history优先预测，读旧PHT符合NBA。ref异步reset把PHT=01、history=0，而原题未给这些值；invalid预测输出X也属ref选择。','保留关键reset契约缺失；自比通过不能批准隐藏初值。','GSHARE','原TB训练/回滚/同周期优先定向加1000随机；valid=0数据用X，计分屏蔽。'),
16:('AUXILIARY','1位同步高reset DFF','posedge clk，r优先q=0否则d，复位前初态未规定；原ref符合。','保留dff/dff8r宽度变体。','DFF','原TB100随机边沿，r随机，不能当独立异步reset检测。'),
17:('DO_NOT_EXECUTE','带dont-care的四变量卡诺图','接口4位x即[3:0]，图标x[1]x[2]/x[3]x[4]涉及不存在x[4]；可能一基编号，但未明确映射。ref16项含X，不能替作者确定变量对应。','保留关键索引契约歧义，不因ref自比通过解除。','KMAP4','原TB100随机，参考X项不判错。'),
18:('AUXILIARY','8位偶校验位','parity=^in，输入加parity后总1数为偶；8位无符号、无reset，全0/全1均0，单1为1。','保留历史parity8同功能。','PARITY','原TB100随机边沿，非256输入全穷举。'),
19:('AUXILIARY','六状态同步Moore机','posedge同步高reset到A；逐行6x2转移与题一致，E/F输出1。非法state给X。separate always结构原ref满足但功能TB不能证明生成结构。','保留与135输入取反后同构图暴露及旧相关标签。','FSM6_COMPLEMENT','原TB200negedge随机reset/w，未定向声明初始reset，早期X可能被屏蔽。'),
20:('DO_NOT_EXECUTE','由一组波形猜四路4位mux','ref c=0/1/2/3选择b/e/a/d，其余f；原波形只在a=a,b=b,d=d,e=e固定时扫c，常量b/e/a/d同样满足已示例。未唯一规定其余输入值行为。','保留欠定契约，不能以常见题型替代规格。','MUX4_UNDERSPEC','TB实际另用12034/56078和随机输入超出原示例，故隐藏约束可影响成绩。'),
21:('AUXILIARY','2输入NOR','1位组合out=~(a|b)，00=>1其余0；无reset。','与22仅端口名不同；历史087 out_nor完整同功能。','NOR2','计数遍历及200随机边沿。'),
22:('AUXILIARY','2输入NOR（不同端口名）','1位组合out=~(in1|in2)，与21同四行真值；无reset。','与21精确功能重复且历史087 out_nor暴露。','NOR2','100随机边沿。'),
23:('AUXILIARY','输入0翻转、1保持的二状态Moore机','同步高reset到B，out=1；state_next=in?state:~state。所有两个state和输入组合有定义。','历史109_fsm1完全同转移/输出，只有reset异步改同步。','FSM_TOGGLE','含reset_test(0)、定向输入及200随机。'),
24:('MAIN_CANDIDATE','组合温控器及风扇','heater=mode&cold，aircon=~mode&hot；两者互斥，fan=heater|aircon|fan_on与ref三元式等价。mode/cold/hot/fan_on四输入共16行包括cold=hot=1均定义，无reset/锁存。','共用mux/门原语，但带互斥制热制冷和风扇联动的整体接口未在冻结历史表发现同功能；已于本轮读取，不称训练未见。','THERMOSTAT','冬夏定向覆盖同时hot/cold与fan_on，加200随机。'),
25:('AUXILIARY','波形完整真值的AND','原波形给出00/01/10/11全四组，唯一二值组合关系q=a&b；不因为waveform形式就判欠定。X/Z行为未要求。','与本轮026及历史087 AND重复。','AND','两次遍历4组合及100随机。'),
26:('AUXILIARY','三输入完整真值/单bit mux','8行f为0,0,1,1,0,1,0,1；ref为minterm2/3/5/7之和，化简f=x3?x1:x2，无reset。','与历史022 mux2to1在sel=x3,b=x1,a=x2映射下完全相同；017为宽度变体。','MUX2','原TB遍历8行；随后repeat(40)仅等待，随机赋值在循环外且紧接finish，不能称40随机向量。'),
27:('AUXILIARY','每三周期恰好两个1输出脉冲','同步高reset到A，s只在A有效；B/C为分组边界，S10/S11记录第一位，S20/S21/S22记录前两位和；第三位使011/101/110进入C(z=1)。下一周期同时采下一组三位的首位，窗口不滑动。','暂未见完全同功能历史，但与计数/FSM原语相关；原题as few states as possible不是功能TB验收项，本轮不声称最小化已证，因此辅助分析。','COUNT2OF3','s持续1/再reset及随机脉冲；没有状态最小化结构检查。'),
28:('AUXILIARY','PS/2三字节边界检测','8位in仅看bit3找第一字节，之后两字节忽略bit3；第三字节后DONE一周期，DONE可直接接下一第一字节。同步高reset BYTE1。','历史154_fsm_ps2data包含同一四状态done路径；本题仅删载荷输出。','PS2','200negedge随机输入/reset；未指定初始reset，初期X可能被屏蔽。'),
29:('DO_NOT_EXECUTE','无reset的反馈XOR触发器','posedge out<=in xor out；原题明确无reset且不规定初态，ref额外initial out=0。合法未初始化寄存器与该ref会产生差异；不把initial写回题或据自比称规格一致。','新增初态契约缺口，参考自一致不解除。','XOR_ACCUMULATOR','100随机边沿，TB未给初始化输入；参考起始0成为隐藏要求。'),
30:('AUXILIARY','XOR的组合两路及寄存一路','1位a/b，assign和always_comb即时a xor b；out_always_ff在posedge采样，初态无规定，无reset。ref功能符合。','与历史087 XOR/031 DFF及本轮026语法练习有关；三种指定语法结构不能由输出TB证明，保留辅助。','XOR_AND_REGISTER','计数遍历加200随机，计分在双边沿，不能证明任意边沿间稳定性。'),
}
scope=read(P/'scope.json');old={x['id']:x for x in read(R/'exploration/20261024/public-rag-all20-reconsider-v1/adoption.json')['rows']}
cal={x['task']:x for x in read(P/'calibration/receipt-audit.json')['rows']};acq=read(P/'acquisition.json')
rows=[]
for s in scope['tasks']:
 rank=s['rank'];decision,title,contract,overlap,family,coverage=notes[rank]
 tb=P/'originals'/s['files']['test.sv']['path'];ref=P/'originals'/s['files']['ref.sv']['path']
 t=tb.read_text();r=ref.read_text();assets=re.findall(r'(?:`include|\$readmem\w*|\$fopen).*',t+r)
 anchors={label:[{'line':j+1,'text':line} for j,line in enumerate(text.splitlines()) if re.search(pattern,line)] for label,text,pattern in [('reference',r,r'module |input |output |assign |always|initial|if \(|case |default:|<=|next ='),('test_sampling',t,r'tb_match =|always @\(posedge clk|stats1.clocks|wait_for_end_of_timestep|TIMEOUT|\$finish|\$random|\$urandom')]}
 rows.append({'rank':rank,'id':s['id'],'category':decision,'meaning_zh':title,'static_contract_review_zh':contract,'overlap_review_zh':overlap,'related_family':family,'coverage_zh':coverage,'prior_adoption_record':old.get(s['id']),'history_exposure':'PREVIOUSLY_READ_ADOPTED20' if rank<=20 else 'READ_IN_THIS_REVIEW_AFTER_SCOPE_FREEZE','training_exposure':'UNKNOWN','reference_is_independent_oracle':False,'reference_qualification':'STATIC_REVIEW_ONLY; same upstream reference+TB','sampling_phase':'TB双边沿active区比较；wait_for_end_of_timestep仅定义未调用；NBA更新后稳定采样未保证','dont_care':'参考X经ref ^ dut ^ ref比较式屏蔽，未知初态不能据零错视为已覆盖','assets_detected':assets,'school_adapter':'THREE_SOURCE_FILES_SUPPORTED' if not assets else 'BLOCKED_ASSETS','calibration':cal[s['id']],'source_bindings':[x for x in acq if x['task']==s['id']],'anchors':anchors})
assert len(rows)==30
with (P/'reference-risk-review.json').open('x',encoding='utf-8') as f:json.dump({'rows':rows,'categories':{c:sum(r['category']==c for r in rows) for c in ('MAIN_CANDIDATE','AUXILIARY','DO_NOT_EXECUTE')},'selection_is_before_retrieval':True,'simulation_retries':0,'no_new_stimulus':True},f,ensure_ascii=False,indent=2)
print({c:sum(r['category']==c for r in rows) for c in ('MAIN_CANDIDATE','AUXILIARY','DO_NOT_EXECUTE')})
