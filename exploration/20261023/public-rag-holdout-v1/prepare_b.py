"""Static qualification only. No network, model, imports of runners, or EDA."""
from pathlib import Path
import json, hashlib, datetime, re
P=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_bytes().decode('utf-8-sig'))
def write(p,obj):
 assert not p.exists(),str(p)
 p.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
a=read(P/'A-lock.json')
assert set(a)=={x.relative_to(P/'A').as_posix() for x in (P/'A').rglob('*') if x.is_file()}
assert all(sha((P/'A'/k).read_bytes())==v for k,v in a.items())
assert sha((P/'A-lock.json').read_bytes())==read(P/'A-seal.json')['a_lock_sha256']
assert not (P/'B-lock.json').exists()
order=read(P/'B/candidate-order.json')['new_candidates']
# Decisions recorded before retrieval. Shared primitives alone do not make a duplicate.
reviews=[
(False,'SPEC_REFERENCE_CONFLICT','水位控制','原文要求水位上升时打开 dfr；参考 A2→B1(水位000→001)给0110，即dfr=0，而下降C1→B2给0111。方向相反，不能改原文或参考。测试包含上升下降序列。'),
(True,'ELIGIBLE','串行二进制补码','任意长度LSB先入的串行补码Moore机，posedge与高有效异步reset明确。不同于并行adder8/ve_addsub、奇偶累计或固定序列检测；串行携带“首次1已见”状态是不同完整契约。复位期间输出由参考固定为0，原文停止转换、复位初态的自然解释仍需用户确认，不增补prompt。'),
(False,'HISTORY_NEAR_DUPLICATE','三输入XNOR/XOR','等价于3位奇偶归约取反；相对历史parity8只是宽度和输出极性变化，保守排除。'),
(False,'WRAPPER_STRUCTURE_CONFLICT','组合子模块','原文明确两A两B子模块实例，且未指定顶层模块名；冻结system只允许一个指定名模块。不能添TopModule要求或静默取消结构要求。'),
(True,'ELIGIBLE','100位向量反序','索引i接99-i的固定排列；不同于历史可变移位/循环旋转，非同函数宽度变体。接口与排列定义完整。'),
(True,'ELIGIBLE','串行字节接收','0起始+8位LSB载荷+1停止、错误停止恢复、仅done时载荷有效、同步高有效reset完整。与framed_parity的固定4位奇偶帧、escape_frame的2位转义token/XOR计数、I2C时钟总线控制均非同一完整契约；共享移位/帧状态原语披露。末句done遇stop按前文“correctly received”解释，错误帧恢复stop不交付；该语境解释须总控核对，不能把参考实现加进prompt。'),
(False,'HISTORY_NEAR_DUPLICATE','有符号加法溢出','核心8位加法与历史adder8/alu8/saturating8/ve_addsub重合，仅符号溢出标志差异；保守排除。'),
(False,'SPEC_AMBIGUITY','补全条件分支','原题标题adder-subtractor与cpu/驾驶端口冲突；只说fix bug，未给未命中条件输出契约，不能从参考补足else语义。'),
(True,'ELIGIBLE','三位向量拆线','明确outv原样输出、o0/o1/o2按位输出；与decoder3的onehot解码、mux8的选择函数不同。没有状态/复位语义缺口。'),
(True,'ELIGIBLE','向量拼接拆分','六个5位输入按列举a..f顺序拼接，末尾二个1，按w/x/y/z顺序拆成32位。参考与列举顺序一致；原文没有显式拼接等式，顺序解释在审阅说明中披露，不写回原题。与历史shift/mux功能不同。'),
(True,'ELIGIBLE','双四输入NAND','两个独立四输入归约NAND，接口齐全。历史ALU含逐位AND但非这两组归约输出，基础门共享不是完整近重复。'),
(False,'HISTORY_NEAR_DUPLICATE','二状态翻转','遇in=0翻转、in=1保持，reset输出1；与event_parity输入反相/初值变化同构，保守排除。原文另未明确clk边沿，不补足。'),
(False,'HISTORY_NEAR_DUPLICATE','组合FSM方程','包含已暴露Prob095四拍shift_ena和Prob096的1101识别子机；组合方程任务形式不同仍实质复用已读结构，保守排除。'),
(True,'ELIGIBLE','向量逻辑门','同时给逐位OR、逻辑OR、按明确次序NOT拼接；与历史ALU单项OR有原语交叉，但完整多输出契约不同。'),
(True,'ELIGIBLE','符号扩展','8→32位符号复制，接口和示例完整；历史signedcmp8的比较结果不同，非仅宽度变体。'),
(True,'ELIGIBLE','NOT门','完整一位反相契约；历史集合没有该完整独立任务。简单程度不作为入选/排除依据。'),
(True,'ELIGIBLE','三反馈寄存器','三支XOR/AND/OR反馈及NOR输出，初态全0与posedge明确；其中一支与event_parity共享原语但完整三状态位系统不同。初始化声明可在单模块表达；可综合性平台适配未校准。'),
(True,'ELIGIBLE','25项两两比较','5标量的全对XNOR矩阵及位序明确；与历史signedcmp8数值大小比较/单一parity输出不同。'),
(False,'HISTORY_NEAR_DUPLICATE','优先编码器','与历史encoder4/leadingzero8为优先位置编码族，仅宽度/扫描方向/valid输出变化，保守排除。'),
(True,'ELIGIBLE','Lemmings方向机','两输入按当前方向响应碰撞，同时碰撞翻向，posedge异步高reset到向左。与event_parity无状态依赖选择输入、单条件翻转不同；非旧ve_fsm三状态图。')]
rows=[];chosen=[]
for r,(eligible,code,meaning,reason) in zip(order,reviews):
 bindings={}; static={}
 for kind,info in r['files'].items():
  f=P/'B/originals'/info['path']; raw=f.read_bytes()
  blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
  assert blob==info['git_blob_sha1']
  bindings[kind]={'path':f.relative_to(P).as_posix(),'sha256':sha(raw),'git_blob_sha1':blob,'bytes':len(raw),'url':f"https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/{info['path']}"}
  text=raw.decode()
  if kind!='prompt.txt':
   static[kind]={'modules':re.findall(r'(?m)^module\s+(\w+)',text),'includes':re.findall(r'`include\s+([^\n]+)',text),'readmem':bool(re.search(r'\$readmem',text))}
   assert not static[kind]['includes'] and not static[kind]['readmem']
 status='EXCLUDED'
 if eligible:
  if len(chosen)<5:chosen.append(r['id']);status='SELECTED_CONDITIONAL'
  else:status='ELIGIBLE_NOT_SELECTED_FIXED_CAP'
 rows.append(dict(rank=r['rank'],id=r['id'],eligible=eligible,status=status,code=code,meaning_zh=meaning,reason_zh=reason,bindings=bindings,static_dependencies=static))
assert len(rows)==20 and len(chosen)==5
write(P/'B/selection.json',dict(utc=utc(),a_lock_sha256=sha((P/'A-lock.json').read_bytes()),candidate_order_sha256=sha((P/'B/candidate-order.json').read_bytes()),selected_ids=chosen,candidate_count=20,eligible_count=sum(r['eligible'] for r in rows),excluded_count=sum(not r['eligible'] for r in rows),selection_rule='first5 eligible in frozen order; selected before retrieval',review_scope='Static source and history review only; all original triples blob-verified; no execution or retrieval yet',independence='Same-upstream reference and test correlated, not independent correctness evidence. Public model training exposure UNKNOWN. Novelty relative to recorded local history only.',rows=rows))
coverage={chosen[0]:'异步reset_test(1)、定向位序列、400个双边沿随机reset/x事件；不是任意长度穷尽。',chosen[1]:'两边沿更新100位随机输入，100个negedge后结束；非2^100穷尽。',chosen[2]:'启动reset、9/10拍低电平的有效/缺失停止序列、800个双边沿随机in/reset事件；out_byte参考为X时不评分。非全载荷/复位相位穷尽。',chosen[3]:'count++驱动10次3位vec，静态可见覆盖0..7并回绕；实际采样数/通过与工具语义未经运行核验。',chosen[4]:'零、1到0x400单比特、交替5位分组和100个双边沿随机输入；不是30位输入穷尽，也未覆盖全部walking-one位置。'}
write(P/'B/coverage.json',dict(per_task=coverage,common=['测试与参考来自同一公开仓库版本，不是独立oracle。','tb_match用参考X作don’t-care；实际错误数/检查次数未知。','TB在posedge/negedge比较，刺激多用NBA赋值；不能将其说成独立的边沿间稳定性或中途复位证明。','所有测试为原文件，无新增向量；依赖静态见RefModule、TopModule、stimulus_gen、tb，无include/readmem。','冻结旧SAT14/32及旧事件检查器尚无这些题的适配/假设审查，当前状态NOT_EVALUATED/NOT_SUPPORTED_PENDING_REVIEW，不机械复制，不省略分母。','后续参考同源校准即使通过也不是独立功能证明；本次0 compile/sim/SAT。']))
write(P/'B-lock.json',{x.relative_to(P/'B').as_posix():sha(x.read_bytes()) for x in sorted((P/'B').rglob('*')) if x.is_file()})
write(P/'B-seal.json',dict(frozen_utc=utc(),b_lock_sha256=sha((P/'B-lock.json').read_bytes()),selection_sha256=sha((P/'B/selection.json').read_bytes()),a_lock_sha256=sha((P/'A-lock.json').read_bytes()),retrievals_so_far=0,model_calls=0,eda_calls=0))
print(json.dumps({'selected':chosen,'eligible':sum(r['eligible'] for r in rows),'excluded':sum(not r['eligible'] for r in rows),'b_lock_sha256':sha((P/'B-lock.json').read_bytes())}))
