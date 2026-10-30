"""Read existing evidence only; create explanatory reports, never rerun experiments."""
from pathlib import Path
import json, hashlib, shutil, zipfile, html, base64
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/pdf'
SHARE = OUT / 'XZY01_1840_evidence'
SHARE.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(TTFont('YaHei', 'C:/Windows/Fonts/msyh.ttc', subfontIndex=0))
BLUE='#183b64'; GRAY='#536173'; TEAL='#087e83'; RED='#b53c3c'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8-sig'))
def para(c, text, x, y, width=499, size=10, color=BLUE):
    style=ParagraphStyle('p',fontName='YaHei',fontSize=size,leading=size*1.6,textColor=HexColor(color),wordWrap='CJK')
    p=Paragraph(text,style); w,h=p.wrap(width,1000);p.drawOn(c,x,y-h);return y-h-9
def header(c, title, sub):
    c.setFillColor(HexColor(BLUE));c.rect(0,770,595,72,fill=1,stroke=0)
    c.setFont('YaHei',19);c.setFillColor(HexColor('#ffffff'));c.drawString(48,807,title)
    c.setFont('YaHei',9);c.drawString(48,785,sub)
def foot(c, n, total):
    c.setFont('YaHei',8);c.setFillColor(HexColor(GRAY));c.drawString(48,25,'XZY01 · Existing evidence review · 2026-10-16');c.drawRightString(547,25,f'{n} / {total}')

def build_share():
    summary=read('evidence/ece-mapped-functional-20261015/summary.json')
    provenance=[]
    for r in summary['results']:
        assert r['checks']==1840 and r['errors']==0 and r['simulation_returncode']==0
        src=ROOT/'workflow/gate-check/returned'/r['functional_return_sha256']
        for name in ['verdict.txt','simulate.exit']:
            f=src/name; dest=SHARE/f"{r['tool']}-{name}"
            shutil.copyfile(f,dest);provenance.append({'source':str(f.relative_to(ROOT)),'copy':dest.name,'sha256':sha(f),'byte_identical':sha(f)==sha(dest)})
        assert r['receipt'] in (src/'verdict.txt').read_text()
    shutil.copyfile(ROOT/'evidence/ece-mapped-functional-20261015/summary.json', SHARE/'verified-results.json')
    path='/staff/ee/dept/public/course_PDK/nangate/freepdk-45nm/lib/NangateOpenCellLibrary_PDKv1_3_v2010_12/Front_End/Liberty/NLDM/'
    commands=f'''XZY01 - Recorded synthesis library setup (reference only; no job executed by this report)

1. School Linux terminal: launch Design Compiler in a separate tcsh
tcsh -f
source /usr/eelocal/synopsys/syn-vx2025.06-sp2/.cshrc
dc_shell

2. Inside dc_shell> (Tcl, NOT Linux shell):
set_app_var target_library [list "{path}NangateOpenCellLibrary_typical.db"]
set_app_var link_library [concat [list "*"] $target_library]
printvar target_library
printvar link_library

The existing synthesis script then analyzes dut.sv, elaborates sequence_detector,
links the design, reads constraints.sdc, and runs compile. Setting a path alone
does not demonstrate successful library loading or synthesis.
Exit DC, then exit tcsh before starting the other environment.

3. School Linux terminal: launch Genus in a separate tcsh
tcsh -f
source /usr/eelocal/cadence/genus211/.cshrc
genus

4. Inside Genus prompt (Tcl, NOT Linux shell):
set_db library [list "{path}NangateOpenCellLibrary_typical.lib"]
get_db library

The existing script next uses read_hdl -sv dut.sv, elaborate sequence_detector,
read_sdc constraints.sdc, syn_generic, syn_map, syn_opt.

Library-setting lines are copied from the archived synthesis.tcl files.
printvar/get_db are optional inspection commands, not additional archived run evidence.
The school library is Nangate Open Cell Library / FreePDK45, typical (1.10 V, 25 C).
The .db and .lib are synthesis inputs. NangateOpenCellLibrary.v is a separate
Verilog cell simulation model. TETRAMAX in the functional check is a model macro,
not a run of the TetraMAX product. No library bytes are included in this package.
'''
    (SHARE/'library-commands.txt').write_text(commands,encoding='utf-8')
    (SHARE/'copy-provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    pdf=SHARE/'XZY01_1840_Verification_Summary.pdf'
    c=canvas.Canvas(str(pdf),pagesize=(595,842));c.setTitle('XZY01 - 1840-check mapped-netlist verification')
    header(c,'综合网表功能验证：1840 次检查','可转发结果说明 / Mapped-netlist functional verification')
    y=742
    for t in [
      '<b>结论：</b>同一历史模型 RTL 经 DC 与 Genus 分别综合后，两份原始综合网表在学校 ECE 环境由 Xcelium 完成固定功能测试，各 1840 次检查、0 错误。',
      '<b>设计：</b>sequence_detector；历史样本 m01__real_overlap__s001__control。学校功能测试日期：2026-10-15。1840 是一次仿真的检查次数，不是 1840 个设计或 1840 次综合。',
      '<b>工具与结果</b>',
      'Synopsys Design Compiler X-2025.06-SP2 → 网表 → Xcelium 23.03-s004：<b>1840 / 0 errors；退出码 0</b>。',
      'Cadence Genus 21.14-s082_1 → 网表 → Xcelium 23.03-s004：<b>1840 / 0 errors；退出码 0</b>。',
      '<b>工艺库来源：</b>学校 ECE 的 course_PDK/nangate/freepdk-45nm 目录；Nangate Open Cell Library，PDKv1_3_v2010_12，typical。Liberty 元数据：process 1.00、1.10 V、25°C，时间 ns、电容 fF。DC 使用 .db，Genus 使用 .lib。',
      '<b>功能仿真配置：</b>原 Nangate Verilog 单元模型，启用内置 TETRAMAX 宏；-nospecify；无 SDF 回标。该宏用于选择模型实现分支，不表示运行了 TetraMAX 工具。',
      '<b>证据链：</b>用户在学校终端手动运行并回传。回执、退出码、RTL、网表、测试台、向量、模型指纹及回传包 SHA-256 已核对；并非远程主机的密码学认证。证据包附原始文本回执及复制哈希。',
      '<b>必须保留的范围：</b>这证明固定测试下的功能通过，不是全输入形式等价或时序签核。DC 仍有 3 条 hold 违例，最差 -0.07 ns；Genus 的 hold 证据未报告。未覆盖 SDF 时序、复位释放时序及多角签核。',
      '<b>历史失败没有删除：</b>默认模型分支的 302 / 300 / 300 个错误记录保留。公开同字节模型的本机排查复现了问题；TETRAMAX 分支负对照仍检出故意引入的功能错误。原 RTL、综合网表、测试台和学校库文件均未因此改写。'
    ]: y=para(c,t,48,y,size=10)
    foot(c,1,2);c.showPage();header(c,'原始回执与可追溯指纹','Receipts copied byte-for-byte; full identifiers in verified-results.json')
    y=741
    for r in summary['results']:
        y=para(c,f"<b>{r['tool'].upper()} 原始回执</b>",48,y,size=12)
        y=para(c,html.escape(r['receipt']),48,y,size=8.5)
        for field,label in [('netlist_sha256','综合网表 SHA-256'),('functional_return_sha256','学校功能回传 ZIP SHA-256')]:
            y=para(c,label,48,y,size=9)
            value=r[field];y=para(c,value[:32]+'<br/>'+value[32:],48,y,size=8.5)
    y=para(c,'<b>两次验证共同使用的输入</b>',48,y,size=12)
    for field,label in [('original_rtl_sha256','原 RTL'),('testbench_sha256','测试台'),('vectors_sha256','输入向量'),('model_sha256','单元仿真模型')]:
        v=summary['results'][0][field];y=para(c,f'{label}：{v[:32]}<br/>{v[32:]}',48,y,size=8.5)
    y=para(c,'附件：dc-verdict.txt / genus-verdict.txt 为原始回执；两个 simulate.exit 文件为原始退出码；verified-results.json 保存完整配置及哈希；copy-provenance.json 记录本次复制来源；library-commands.txt 是分环境的库配置命令。',48,y,size=9)
    assert y>45,y
    foot(c,2,2);c.save()
    hashes={p.name:sha(p) for p in SHARE.iterdir() if p.is_file() and p.name!='SHA256SUMS.json'}
    (SHARE/'SHA256SUMS.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    z=OUT/'XZY01_1840_evidence.zip'
    with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as f:
        for p in SHARE.iterdir():
            if p.is_file():f.write(p,p.name)
    print(pdf);print(z)

def build_experiments():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from PIL import Image
    plt.rcParams.update({'font.family':'Microsoft YaHei','axes.unicode_minus':False,'font.size':12})
    folder=OUT/'XZY01_experiment_report';folder.mkdir(exist_ok=True)
    evidence={}
    def j(rel):
        evidence[rel]=sha(ROOT/rel);return read(rel)
    def bind(rel): evidence[rel]=sha(ROOT/rel)
    e='exploration/20261011/'
    singles=j('evidence/mutation-v1/cases.json')
    single=next(x for x in singles if x['task']=='sticky_alarm' and x['diagnosis'].get('shortest_counterexample',{}).get('bits')=='111' and x['public_before']=='PUBLIC_CHECK_PASS')
    compounds=j(e+'runs/compound-v1/cases.json')
    double=next(x for x in compounds if x['id']=='rt_sequence__edge_00_S1__edge_03_S0')
    reference=j('benchmarks/paired-v1/rt_sequence/reference.json')
    delayed=j(e+'runs/delayed-v1/cases.json')[0]
    hist=j(e+'runs/r1b-v2/history-results.json')
    reset=j(e+'runs/timed-calibration-v2/plan.json')['events']['mid']
    stall=j(e+'handshake-dev-v1/calibration-v1/rtl/stall_data_break/normalized-trace.json')
    stale=j(e+'handshake-dev-v2/calibration-v2/rtl/shared_reset_stale/verdict.json')
    tx='exploration/20261015/transaction-alignment-v1/run-v1/'
    ir=j(tx+'02_legal_stuttering/ir-assessment.json');rtl=j(tx+'02_legal_stuttering/rtl-assessment.json')
    total=j(tx+'summary.json')
    assert len([x for x in singles if x['is_fault']])==163
    assert len([x for x in compounds if x['is_fault']])==3119
    assert double['public_v1']=='PUBLIC_CHECK_PASS' and double['public_v2']=='PUBLIC_CHECK_FAIL'
    assert len(hist)==24 and sum(x['source']['original_status']=='PASS' for x in hist)==17
    assert sum(x['executed'] for x in total['results'])==11
    assert stale['errors'][0]['cycle']==10 and stale['accepted'][1]['cycle']==11
    def graph(ir,bits):
        state=ir['reset']['state']; transitions={(x['from'],x['input']):x['to'] for x in ir['transitions']};out={x['name']:x['output'] for x in ir['states']};a=[]
        for bit in bits: state=transitions[state,int(bit)];a.append(str(out[state]))
        return ''.join(a)
    # This only formats archived finite graphs; no simulation or experiment execution.
    stickyref=j('benchmarks/paired-v1/sticky_alarm/reference.json')
    assert graph(stickyref,'111')=='011' and graph(single['ir'],'111')=='010'
    assert graph(reference,delayed['word'])=='000000010001'
    assert graph(delayed['ir'],delayed['word'])=='000000010000'
    def tablefig(n,title,subtitle,cols,rows,note,bad=()):
        fig,ax=plt.subplots(figsize=(12,4.3));fig.patch.set_facecolor('#f4f7fb');ax.set_facecolor('#f4f7fb');ax.axis('off')
        fig.text(.055,.91,title,size=19,color=BLUE,weight='bold')
        fig.text(.055,.83,subtitle,size=11,color=GRAY)
        t=ax.table(cellText=rows,colLabels=cols,loc='center',cellLoc='center',bbox=[0,.17,1,.65])
        t.auto_set_font_size(False);t.set_fontsize(12 if len(cols)<9 else 11)
        for (r,col),cell in t.get_celld().items():
            cell.set_edgecolor('#d6dfeb');cell.set_text_props(color=BLUE)
            cell.set_facecolor('#e8eff7' if r==0 else '#ffffff')
            if (r,col) in bad:cell.set_facecolor('#fce5e2');cell.set_text_props(color=RED,weight='bold')
        fig.text(.055,.08,note,size=11,color=TEAL)
        fig.subplots_adjust(left=.055,right=.945,bottom=.12,top=.82)
        p=folder/f'{n:02d}-sample.png';fig.savefig(p,dpi=180,facecolor=fig.get_facecolor());plt.close(fig);return p
    figures=[]
    figures.append(tablefig(1,'报警一旦置位，应保持到复位','实际人工变体：'+single['id'],['上升沿后采样','第 1 拍','第 2 拍','第 3 拍'],[['输入','1','1','1'],['正确输出','0','1','1'],['错误输出','0','1','0']], '只改一条转移：报警态收到 1 时，错误返回初态。红格是首次分歧。',[(3,3)]))
    changes=[]
    for a,b in zip(reference['transitions'],double['ir']['transitions']):
        if a!=b:changes.append([f"{a['from']} 收到 {a['input']}",a['to'],b['to']])
    assert len(changes)==2
    figures.append(tablefig(2,'两条转移一起改，旧公开测试仍放过','实际变体：'+double['id'],['修改位置 / 观察','正确版本','错误版本'],changes+[['输入 0001 后输出',graph(reference,'0001'),graph(double['ir'],'0001')]], '此错误变体：旧公开漏检，增强公开检出。整轮 3,119 个 IR 故障中，50 个做 RTL 仿真。',[(1,2),(2,2),(3,2)]))
    word=delayed['word']
    figures.append(tablefig(3,'前 11 位都一样，第 12 位才暴露','实际 rt_sequence 人工延迟触发样本；以下为复位后各输入采样位置', ['位置']+list(map(str,range(1,13))),[['输入']+list(word),['正确']+list(graph(reference,word)),['错误']+list(graph(delayed['ir'],word))], '固定测试漏检；新见证和有界 SAT 检出。SAT 的步号另含初始化/复位，不能混作位序。',[(3,12)]))
    w=hist[0]['results'][0]['witness'];assert w['message']=='Independent testbench found 1 mismatches'
    bind(e+'runs/r1b-v2/history/00_rt_sequence/14/witness/verdict.txt')
    figures.append(tablefig(4,'历史模型 RTL：求解器找输入，仿真再确认','真实历史样本：fsm48 / m02__rt_sequence__prose__s001；未修改模型 RTL', ['证据步骤','这份代码的实际记录'],[['旧判题','FUNCTION_FAIL'],['SAT 界限 14','找到反例；solver mismatch step = 10'],['交给 Icarus 的输入','先复位，然后 01001001'],['独立回放','18 次检查，1 个不符'],['另一界限 32','同一份代码也找到反例']], '整轮是 7 份已知失败 × 2 个界限 = 14 条反例；17 份原通过未发现新反例。'))
    bind(e+'runs/timed-calibration-v2/sync_mid/simulate.stdout.log')
    rows=[['clk']+[str(reset[k]['clk']) for k in range(3,7)],['rst_n（0 为复位）']+[str(reset[k]['reset']) for k in range(3,7)],['参考输出']+[str(reset[k]['expected']) for k in range(3,7)],['错误同步复位输出','1','1','1','1']]
    figures.append(tablefig(5,'没有新时钟沿，异步复位也应该清零','人工校准样本 sync_mid；先正确初始化，再在中途拉低 rst_n', ['事件编号','3','4','5','6'],rows,'事件 5：clk 保持 0，rst_n 从 1 变 0；应输出 0，实际仍为 1。',[(4,3),(4,4)]))
    selected=stall[4:10]
    figures.append(tablefig(6,'接收方还没准备好，数据不能偷偷变','真实执行的手写 RTL：stall_data_break，观察 consumer0', ['周期']+[str(x['cycle']) for x in selected],[['valid']+[str(x['m'][0]['valid']) for x in selected],['ready']+[str(x['m'][0]['ready']) for x in selected],['data']+[str(x['m'][0]['data']) for x in selected]],'周期 4 开始等待；周期 5 起反复改变数据，违反稳定性。周期 9 才发生交付。',[(3,k) for k in range(2,7)]))
    figures.append(tablefig(7,'复位取消了旧包裹，旧包裹却又被送出','实际手写 RTL：shared_reset_stale；数值用十进制表示', ['周期','输入 / 消费事件','判据含义'],[['3','接受旧数据 17','旧 epoch 的事务'],['4','consumer0 收到 17','consumer1 尚未收到'],['8–9','复位；取消 consumer1 待交付 17','旧事务不应跨复位存活'],['10','consumer1 却收到旧数据 17','UNEXPECTED_TRANSACTION'],['11','才接受新数据 161','不能为周期 10 的旧输出作解释']], '故障抓到了；实际分类与预声明不一致，因此完整类别校准仍是 15/16。',[(4,1),(4,2)]))
    fig,ax=plt.subplots(figsize=(12,4.3));fig.patch.set_facecolor('#f4f7fb');ax.set_facecolor('#f4f7fb')
    names=['IR 接受','IR 交付','RTL 接受','RTL 交付']; colors=['#087e83','#d88a22','#7159a6']
    for k,items in enumerate([ir['spec']['accepted'],ir['spec']['delivered'][0],rtl['spec']['accepted'],rtl['spec']['delivered'][0]]):
        yy=3-k;ax.hlines(yy,2,15,color='#d6dfeb',linewidth=2)
        for a,(d,color) in enumerate(zip(items,colors)):
            ax.scatter(d['cycle'],yy,s=150,c=color,marker='o' if k%2==0 else '^',zorder=3)
            ax.text(d['cycle'],yy+.18,f"{'ABC'[a]}={d['beat'][0]}",ha='center',size=10,color=BLUE)
    ax.set_yticks(range(4),names[::-1]);ax.set_xticks(range(3,15));ax.set_xlim(2,15);ax.set_ylim(-.4,3.55);ax.set_xlabel('PRE 握手采样周期（同一 epoch）');ax.spines[['top','right','left']].set_visible(False)
    fig.text(.055,.92,'交付时间不同，事务顺序仍然相同',size=19,color=BLUE,weight='bold')
    fig.text(.055,.84,'实际 case 02_legal_stuttering：RTL 加入两拍延迟；图示 consumer0，consumer1 相同。',size=11,color=GRAY)
    fig.text(.055,.045,'圆点 = 接受；三角 = 交付。按事务身份 A/B/C 对齐，而不是硬对齐每一拍输出。',size=11,color=TEAL)
    fig.subplots_adjust(left=.12,right=.95,top=.73,bottom=.21);p=folder/'08-sample.png';fig.savefig(p,dpi=180);plt.close(fig);figures.append(p)

    sections=[
      dict(title='1. 单处人工故障校准',tag='开发集人工故障 · 检查器改进',source='五个已有开发题的正确参考 IR：序列检测、粘滞报警、奇偶状态、延迟请求与去抖。对状态转移、输出或复位规则逐次只改一处；排除语义等价变体，留下 163 个错误变体。',flow='正确参考 → 单处编辑 → 精确有限状态图确认有错 → 旧公开检查 → 为漏检构造反例 → 独立程序参考核对 → 贪心选出 12 个新增公开测试 → 固定检查复测。另生成对应人工 RTL，检查它是否忠实实现所改 IR。',idea='先故意制造“答案已知的错误”，测量检查器的盲点。用 25 个组合校准“规格→IR”与“IR→RTL”等可观察错误关系，避免把所有失败混在一起。',result='旧公开检出 133/163（81.6%）；增强公开检出 163/163。五题族新增测试数为 8、1、0、1、2，总计 12。25/25 诊断组合符合预期。原固定隐藏测试也检出这 163 个故障。',limit='12 个新测试来自这批开发故障，因此 100% 是开发集覆盖率，不是未知错误检出率或模型成功率。人工参考与判据提供交叉核对，但不是独立外部团队认证。',refs=['MUTATION_FINDINGS.md','evidence/mutation-v1/cases.json','evidence/mutation-v1/summary.json']),
      dict(title='2. 双处编辑故障探索',tag='冻结检查器复测 · 受限组合故障',source='仍使用上述五个开发题；按限定编辑规则同时改变两个不同字段，得到 3,119 个不等价 IR 变体。这些是少量题目的派生错误，不是 3,119 个独立设计。',flow='正确 IR → 枚举两处编辑 → 排除等价情况 → 用已冻结的旧/增强公开检查比较 → 每题按枚举顺序取前 10 个故障做 RTL 检查，共 50 个。另查正确实现与不改变语义的改写。',idea='两处改动可能互相掩盖，不能由“单处全检出”直接推断组合错误也能检出。本轮使用上一轮冻结的增强判据，不根据新结果继续调参。',result='IR 层：旧公开漏 176/3,119，增强公开漏 0。50 个 RTL 故障候选均被隐藏仿真检出，并均与其错误 IR 行为一致。',limit='人工、受限、开发题上的结果。RTL 子集按枚举顺序选择，并非随机代表样本；不能把 IR 全量结果表述为 3,119 次 RTL 仿真。',refs=[e+'RESULTS.md',e+'runs/compound-v1/cases.json',e+'runs/compound-v1/simulation-results.json']),
      dict(title='3. 延迟触发故障',tag='人工构造固定测试盲区 · 有界求解',source='五个开发题分别加入匹配特定 12 位序列的额外状态；前缀偏离触发词时转回正常逻辑。它们是刻意避开已有固定测试的错误，不是模型自然输出。',flow='选择触发词 → 构造额外前缀状态 → 核对所有长度 0–11 的输入 → 运行旧公开/隐藏测试 → 添加触发输入见证 → 用有界 SAT 搜索并检查反例。',idea='固定试题只抽查有限输入。SAT 则在给定范围内寻找“能让参考与实现不一致的输入”；把固定测试通过和更强正确性证据区分开。',result='五个案例在旧公开及旧隐藏测试中全漏检；新见证与 SAT 均检出 5/5。每题长度 0–11 共 4,095 条输入保持一致，五题合计 20,475 条。SAT 使用界限 14。',limit='故障被专门设计为躲开旧测试，不能用 5/5 推算 AI 自然错误频率。图中的第 12 个输入位置与 SAT 的初始化/复位步号不是同一计数。',refs=[e+'RESULTS.md',e+'runs/delayed-v1/cases.json',e+'runs/delayed-v1/summary.json',e+'runs/formal-v1/summary.json']),
      dict(title='4. R1b：历史 RTL 有界检查',tag='历史真实模型输出 · 本轮零模型调用',source='从历史 fsm48、paired-a32 与 paired-b64 输出中选出 24 份 RTL：原固定测试 17 份通过、7 份失败。保留原输出字节与来源哈希，不修改模型答案。',flow='历史 RTL 与参考 → 构造输出差异检查电路 → Yosys 在 14 与 32 两个界限求解 → 保存反例输入 → Icarus 独立回放 → 核对实际不符与回执。',idea='求解器报告的反例也需要仿真复现。双工具交叉验证可以排查转换和判题错误，但同一参考规格仍可能带来共同盲区。',result='7 份已知失败在两个界限都产生反例，共 14 条，全部仿真复现。17 份原通过没有发现新反例。本轮新增自然错误发现数为 0。',limit='“未发现反例”只限所用建模与界限；不代表无限时域正确。14 条反例来自 7 份失败代码，不能当成 14 个独立失败设计。',refs=[e+'R1B_RESULTS.md',e+'runs/r1b-v2/history-results.json',e+'runs/r1b-v2/history/00_rt_sequence/14/witness/verdict.txt']),
      dict(title='5. R1c：事件与复位复测',tag='历史 RTL 复查 + 人工时序校准',source='候选池有 99 条历史 PASS 记录、78 个不同 RTL 字节哈希；按题族/模型分配选出其中 64 份，14 份未选。覆盖五个题族。图示则是用来校准检查器的人工同步复位错误，不能计为历史代码新错误。',flow='先用正确/错误 RTL 校准事件判据 → 枚举输入前缀、时钟高低电平、复位脉冲与输入组合 → 独立程序参考和状态图交叉核对期望 → 对 64 份历史 RTL 实际仿真。',idea='只在时钟沿检查容易漏掉异步复位、无时钟沿保持和输入泄漏问题。补充实验先正确初始化，再单独制造目标事件，避免把初始 X 误当作目标故障证据。',result='64/64 历史 RTL 通过，新增自然错误 0。五题族各 90,972 个参考事件，合计 454,860 次独立期望核对。图示人工错误在事件 5、6 被检出。',limit='纠正旧简称：64 是去重选出的 RTL 文件数，不只是 64 个事件配置；454,860 是参考事件核对数，不是 64 次仿真事件总和。数字仿真不覆盖物理亚稳态或真实 setup/hold。',refs=[e+'R1C_RESULTS.md',e+'runs/timed-reset-v1/selection.json',e+'runs/timed-calibration-v2/plan.json',e+'runs/timed-calibration-v2/sync_mid/simulate.stdout.log']),
      dict(title='6. 握手判据 v1',tag='人工轨迹与手写 RTL · 事务交付判据',source='22 条人工编排轨迹，以及 10 个实际编译仿真的手写 RTL 案例。场景来自有限广播/握手开发契约，含合法延迟、停顿、丢失、重复、损坏及无效输入。',flow='先声明输入计划和合法规则 → 采集 valid/ready/data/last → 在 valid 与 ready 同时为 1 的采样点记一次交付 → 每个接收方独立维护待交付队列 → 检查顺序、内容、稳定性和有限排空。',idea='像逐个登记包裹：接收方暂时不能收时，发送方要保持包裹不变。合法电路允许不同延迟，判据不应强求所有波形逐拍等于某个实现。',result='22 条轨迹预期分类全部匹配。10 个真实执行的手写 RTL 中，3 个合法实现通过，7 个人工故障检出。图示周期 5 已出现等待中数据改变。',limit='实际运行 RTL 工具，不等于错误来自 AI。开发契约、参考与检查器仍有同源风险；有限排空通过不代表任意停顿长度下都正确。',refs=[e+'handshake-dev-v1/RESULTS.md',e+'handshake-dev-v1/CONTRACT.md',e+'handshake-dev-v1/calibration-v1/rtl/stall_data_break/normalized-trace.json',e+'handshake-dev-v1/calibration-v1/rtl/stall_data_break/verdict.json']),
      dict(title='7. 握手判据 v2',tag='保留负结果 · 复位取消与握手因果',source='新增有限 8 条手推轨迹和 8 个手写 RTL 案例，围绕中途复位、接受前提前输出、另一种合法双队列缓冲结构。保留 v1 原证据。',flow='冻结复位取消规则及预期类别 → 同时安排合法结构与人工故障 → 记录 80 周期轨迹 → 按复位划分 epoch → 逐项核对接受、取消、交付，以及完整错误类别。',idea='“先送出、后接受”即使最终数据序列相同，也违反因果关系。复位则切断新旧事务：被取消的旧数据不能在复位后重新冒出。',result='通过/失败状态 16/16 与预期一致；完整错误类别 15/16 一致。图示本应失败且确实失败，但原预声明 DATA_OR_ORDER_FAIL，实际为 UNEXPECTED_TRANSACTION；校准失败状态保持。',limit='抓到错误与准确命名错误是两个指标，不能只展示 16/16。合法提前 valid 只在该固定 ready 场景验证，不能泛化为任意组合握手都安全。',refs=[e+'handshake-dev-v2/RESULTS.md',e+'handshake-dev-v2/calibration-v2/summary.json',e+'handshake-dev-v2/calibration-v2/rtl/shared_reset_stale/verdict.json']),
      dict(title='8. 事务域 IR / RTL 对齐',tag='有限人工映射 · 三路判断',source='以当前 R6 寄存器表达式 IR 建立人工广播映射，再与手写 RTL 配对。预声明 12 个场景：11 个执行，1 个因复位规则含糊而事先排除。它们尚非新外部保留任务。',flow='冻结 PRE/POST 采样、复位 epoch 与输入身份 → IR 和 RTL 各运行自己的合法输入驱动 → 先分别检查是否满足规格 → 再按事务身份及取消集合比较 → 输出通过、失败或不可评估。',idea='比较的是同一事务有没有正确到达，而非每一拍是否一样。若复位前双方接受的输入集合不同，直接比较最终序列可能冤枉合法实现，需要明确“不具备可比条件”。',result='11 个执行案例的意图比较：6 通过、2 人工故障检出、3 不可评估。3 个原因分别是接受/取消集合不同、输入违约、采样缺失。另 1 项未执行。图示合法不同延迟仍通过。',limit='只验证有限映射与固定场景，不能宣称整个 IR 语言与所有 RTL 等价。未证明复杂外部任务上的自然错误定位价值；不把不可评估计作 RTL 故障。',refs=['exploration/20261015/transaction-alignment-v1-report/RESULTS.md',tx+'summary.json',tx+'02_legal_stuttering/ir-assessment.json',tx+'02_legal_stuttering/rtl-assessment.json'])
    ]
    pdf=folder/'XZY01_Eight_Experiments_Illustrated.pdf'
    c=canvas.Canvas(str(pdf),pagesize=(595,842));c.setTitle('XZY01 - 八项离线实验图文报告')
    for i,(s,figpath) in enumerate(zip(sections,figures),1):
        header(c,s['title'],s['tag']);y=743
        for label,key in [('数据从哪里来','source'),('怎样修改 / 测试','flow'),('为什么这样设计','idea')]:
            y=para(c,f"<b>{label}：</b>{html.escape(s[key])}",48,y,size=10)
        assert y>490,(i,y)
        c.drawImage(str(figpath),48,y-204,width=499,height=179,preserveAspectRatio=True)
        y=para(c,'<b>实际结果：</b>'+html.escape(s['result']),48,y-222,size=10)
        y=para(c,'<b>结论边界：</b>'+html.escape(s['limit']),48,y,size=10,color=RED)
        y=para(c,'<b>证据索引</b>（均相对于 outputs/rtl-batch；图是原始记录的注释重绘，不是工具截图）',48,y,size=8,color=GRAY)
        for ref in s['refs']:
            bind(ref);y=para(c,html.escape(ref),48,y,size=6.8,color=GRAY)
        assert y>35,(i,y)
        foot(c,i,8);c.showPage()
    c.save()
    cards=[]
    for i,(s,f) in enumerate(zip(sections,figures),1):
        data=base64.b64encode(f.read_bytes()).decode()
        content=''.join(f'<p><b>{label}：</b>{html.escape(s[key])}</p>' for label,key in [('数据来源','source'),('修改与验证流程','flow'),('设计思路','idea')])
        refs=''.join(f'<li>{html.escape(r)}</li>' for r in s['refs'])
        cards.append(f'<article id="s{i}"><span class="tag">{s["tag"]}</span><h2>{s["title"]}</h2>{content}<img src="data:image/png;base64,{data}" alt="实验{i}原始记录的可视化样本"><p class="result"><b>结果：</b>{s["result"]}</p><p class="limit"><b>局限：</b>{s["limit"]}</p><details><summary>原始证据索引</summary><ul>{refs}</ul></details></article>')
    doc='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>XZY01 八项实验图文报告</title><style>body{margin:0;background:#eef3f8;color:#183b64;font:16px/1.8 "Microsoft YaHei",sans-serif}main{max-width:1040px;margin:auto;padding:30px}header,article{background:white;padding:30px 40px;border-radius:16px;margin-bottom:24px}h1{font-size:32px}h2{margin-top:6px}.tag{color:#087e83;font-size:14px}img{width:100%;border-radius:12px}p{margin:12px 0}.result{background:#eaf5f2;padding:12px}.limit{background:#fff3ed;padding:12px;color:#9d3d28}nav a{display:inline-block;margin:6px 14px 6px 0;color:#087e83}details{font-size:12px;overflow-wrap:anywhere}button{border:0;background:#183b64;color:white;padding:10px 18px;border-radius:6px}@media print{body{background:white}main{padding:0}nav,button{display:none}article{page-break-before:always;padding:16px}header{padding:16px}}</style><main><header><span class="tag">XZY01 · 2026-10-16 · 基于已归档证据</span><h1>八项实验：检查器怎样逐步变可靠？</h1><p>先用人为可控错误找盲区，再复查历史模型代码，最后把判据推进到握手与事务交付。每项配一张实际案例的注释重绘。</p><p><b>总体判断：</b>这些实验支持“检查与诊断方法有了更明确的覆盖和边界”。其中历史模型复查没有发现新增自然错误；人工故障检出不能当成显式 IR 或反馈提高模型成功率的证据。</p><p>术语：IR = 可执行行为草稿；RTL = 电路实现代码；参考 = 预先规定正确行为的程序/规则；反例 = 能使实现违反规则的一组输入。</p><nav>'''+''.join(f'<a href="#s{i}">{i}. {s["title"].split(". ",1)[1]}</a>' for i,s in enumerate(sections,1))+'''</nav><button onclick="window.print()">打印 / 保存 PDF</button></header>'''+''.join(cards)+'''<p>本次仅阅读原证据、提取示例并生成报告；没有调用模型、重新运行实验或修改冻结证据。HTML 内嵌全部图，可单文件转发；证据索引需回到项目中查阅。</p></main></html>'''
    (folder/'XZY01_Eight_Experiments_Illustrated.html').write_text(doc,encoding='utf-8')
    (folder/'source-hashes.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    assert all(sha(ROOT/r)==v for r,v in evidence.items())
    (folder/'sample-selection.json').write_text(json.dumps({'single':single['id'],'double':double['id'],'delayed':delayed['word'],'historical':hist[0]['source'],'figures_are':'Annotated redraws of archived data, not tool screenshots','new_model_calls':0,'new_experiment_runs':0},ensure_ascii=False,indent=2),encoding='utf-8')
    thumbs=[]
    for p in figures:
        im=Image.open(p).convert('RGB');im.thumbnail((1000,360));thumbs.append(im)
    sheet=Image.new('RGB',(2000,1440),'#ffffff')
    for k,im in enumerate(thumbs):sheet.paste(im,((k%2)*1000,(k//2)*360))
    sheet.save(folder/'all-eight-samples.png')
    print(pdf);print('Evidence files bound:',len(evidence))

if __name__=='__main__':
    import sys
    if '--experiments' in sys.argv: build_experiments()
    else: build_share()
