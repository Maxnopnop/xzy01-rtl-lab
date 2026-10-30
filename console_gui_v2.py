"""Native additive console. No API requests on opening, importing or previewing."""
import html
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import uuid
import console_bridge as b
import console_school as school

class Console:
    def __init__(self,root):
        self.root=root;self.package=None;self.release=None;self.rows=[];self.busy=False;self.events=queue.Queue();self.school_record=None
        root.title('XZY01 控制台 v2 · OpenRouter 与冻结实验')
        root.geometry('1280x850');root.minsize(1000,700)
        top=ttk.Frame(root,padding=10);top.pack(fill='x')
        ttk.Label(top,text='已有结果优先 · 导入/预览不调用 API · 学校人工单例',font=('Microsoft YaHei UI',14,'bold')).pack(anchor='w')
        controls=ttk.Frame(top);controls.pack(fill='x')
        for title,cmd in [('读取新96',lambda:self.load_history('new96')),('读取旧240',lambda:self.load_history('old240')),('读取全部336',lambda:self.load_history(None)),('导入冻结包',self.import_package),('选择放行文件',self.choose_release),('打开旧控制台',self.legacy)]:self.button(controls,title,cmd)
        keybar=ttk.Frame(top);keybar.pack(fill='x')
        ttk.Label(keybar,text='OpenRouter Key（仅内存）').pack(side='left')
        self.key=tk.StringVar();ttk.Entry(keybar,textvariable=self.key,show='*',width=32).pack(side='left',padx=5)
        self.button(keybar,'清除密钥',lambda:self.key.set(''))
        ttk.Label(keybar,text='https://openrouter.ai/api/v1/chat/completions').pack(side='left')
        tabs=ttk.Notebook(root);tabs.pack(fill='both',expand=True,padx=10)
        self.main=ttk.Frame(tabs);self.sch=ttk.Frame(tabs,padding=10)
        tabs.add(self.main,text='实验 / 本机验证');tabs.add(self.sch,text='学校单例 / 回传')
        cols=('dataset','ordinal','task','condition','model','status','fixed_test','synthesis','budget')
        self.table=ttk.Treeview(self.main,columns=cols,show='headings',selectmode='browse',height=13)
        for k in cols:self.table.heading(k,text=k);self.table.column(k,width=125 if k!='status' else 190)
        self.table.pack(fill='both',expand=True)
        scroll=ttk.Scrollbar(self.main,orient='horizontal',command=self.table.xview);scroll.pack(fill='x');self.table.configure(xscrollcommand=scroll.set)
        self.table.bind('<<TreeviewSelect>>',lambda e:self.details())
        bar=ttk.Frame(self.main);bar.pack(fill='x')
        for title,cmd in [('检查放行（不联网）',self.preflight),('运行所选一个槽（消耗API）',self.run),('导出隐藏Key终端入口',self.launcher),('所选 RTL 本机复验＋Yosys',self.local),('导出当前结果报告',self.report)]:self.button(bar,title,cmd)
        self.detail=ScrolledText(self.main,height=10,wrap='word');self.detail.pack(fill='both',expand=True)
        ttk.Label(self.sch,text='先在实验页选一个槽；打包只写共享目录，命令由用户在学校终端执行。').pack(anchor='w')
        schoolbar=ttk.Frame(self.sch);schoolbar.pack(fill='x')
        self.tool=tk.StringVar(value='vcs');ttk.Combobox(schoolbar,textvariable=self.tool,values=['vcs','xcelium','dc','genus'],state='readonly',width=12).pack(side='left')
        for title,cmd in [('打包一个案例',self.pack),('载入已打包记录',self.load_school_record),('校验共享文件并复制命令',self.copy_command),('回收结果并验 hash',self.collect),('查看已有 slot25 学校结果',self.school_results)]:self.button(schoolbar,title,cmd)
        recoverybar=ttk.Frame(self.sch);recoverybar.pack(fill='x')
        self.button(recoverybar,'复制仅检查共享命令',lambda:self.copy_command('check'))
        self.button(recoverybar,'复制仅补传命令（不重跑EDA）',lambda:self.copy_command('ship'))
        self.schooltext=ScrolledText(self.sch,height=20,wrap='word');self.schooltext.pack(fill='both',expand=True)
        self.status=tk.StringVar(value='打开窗口未调用 API；历史批只读。')
        ttk.Label(root,textvariable=self.status,padding=10).pack(fill='x')
        self.root.after(100,self.poll);root.protocol('WM_DELETE_WINDOW',self.close)
        self.load_history(None)
        self.school_results()

    def button(self,parent,title,cmd):
        ttk.Button(parent,text=title,command=lambda:self.guard(cmd)).pack(side='left',padx=3,pady=5)
    def guard(self,cmd):
        try:
            b.require(not self.busy,'任务执行中，请等待')
            cmd()
        except Exception as e:messagebox.showerror('未执行',self.redact(str(e)),parent=self.root)
    def redact(self,text):
        secret=self.key.get()
        return text.replace(secret,'[REDACTED]') if secret else text
    def background(self,fn,done):
        self.busy=True;self.status.set('处理中；请等待，勿关闭窗口。')
        def work():
            try:self.events.put((True,fn(),done))
            except Exception as e:self.events.put((False,str(e),None))
        threading.Thread(target=work,daemon=True).start()
    def poll(self):
        try:
            ok,value,done=self.events.get_nowait();self.busy=False
            if ok:done(value)
            else:messagebox.showerror('任务停止',self.redact(value),parent=self.root)
            self.status.set('操作结束；未自动重试。')
        except queue.Empty:pass
        self.root.after(100,self.poll)
    def show(self,widget,obj):
        widget.configure(state='normal');widget.delete('1.0','end');widget.insert('end',self.redact(json.dumps(obj,ensure_ascii=False,indent=2)));widget.configure(state='disabled')
    def display(self,rows):
        self.rows=rows
        for iid in self.table.get_children():self.table.delete(iid)
        for n,r in enumerate(rows):self.table.insert('', 'end', iid=str(n),values=tuple(r.get(k,'') for k in ('dataset','ordinal','task','condition','model','status','fixed_test','synthesis'))+(r.get('output_budget') or '无显式token硬上限',))
        self.status.set('已读取 %d 槽；没有模型调用。'%len(rows))
    def load_history(self,name):
        self.package=None;self.release=None
        self.display(b.historical_rows(name) if name else b.history())
    def selected(self):
        ids=self.table.selection();b.require(bool(ids),'请先选择一个槽')
        return self.rows[int(ids[0])]
    def details(self):
        if self.table.selection():self.show(self.detail,self.selected())
    def import_package(self):
        p=filedialog.askopenfilename(title='选择 console-package.json',filetypes=[('JSON','*.json')])
        if p:
            self.package=b.Package(p);self.release=None;self.display(self.package.rows())
    def choose_release(self):
        p=filedialog.askopenfilename(title='选择总控审核的放行 JSON',filetypes=[('JSON','*.json')])
        if p:self.release=p;self.status.set('已选择放行文件；尚未核验、未调用 API。')
    def preflight(self):
        b.require(self.package is not None,'历史结果只读；新实验须导入冻结包')
        b.require(self.release is not None,'请先选择审核放行文件')
        s=self.package.gate(self.release,self.selected()['id'])
        self.show(self.detail,dict(ready=True,slot=s['id'],manifest_sha256=self.package.identity,max_calls=self.package.data['max_calls'],network_requests=0))
    def run(self):
        self.preflight();row=self.selected()
        secret=self.key.get() or os.environ.get('OPENROUTER_API_KEY','')
        b.require(bool(secret),'请填写隐藏密钥')
        if messagebox.askyesno('执行一个已放行槽','将发送一次真实 POST；可能消耗额度。未知结果不重试。继续？',parent=self.root):
            self.background(lambda:self.package.dispatch(self.release,row['id'],secret),lambda r:(self.display(self.package.rows()),self.show(self.detail,r)))
    def launcher(self):
        b.require(self.package is not None and self.release is not None,'先导入冻结包并选择放行文件')
        p=filedialog.asksaveasfilename(title='保存终端入口（不含密钥）',initialfile='Start-OpenRouter-One.ps1',defaultextension='.ps1')
        if p:
            from console_cli import export_launcher
            export_launcher(self.package.path,self.release,p)
            self.status.set('已生成隐藏Key终端入口，未执行。')
    def local(self):
        row=self.selected();source=Path(row['job_dir']);b.require((source/'dut.sv').exists(),'该槽没有保存 RTL')
        receipt=row.get('receipt');expected=receipt[0][1] if receipt else row.get('expected_checks')
        b.require(type(expected) is int,'缺固定检查数，不能猜测')
        dest=b.STATE/'local'/('replay-'+uuid.uuid4().hex[:12])
        self.background(lambda:b.local_replay(source,dest,expected,row.get('top','TopModule'),row.get('assets',[])),lambda r:self.show(self.detail,dict(r,evidence=str(dest))))
    def report(self):
        path=b.STATE/('report-'+uuid.uuid4().hex[:12]+'.html')
        path.parent.mkdir(parents=True,exist_ok=True)
        headers=['dataset','id','status','fixed_test','synthesis','messages_actual_sha256','output_budget','usage','cost']
        body=''.join('<tr>'+''.join('<td>'+html.escape(str(r.get(k)))+'</td>' for k in headers)+'</tr>' for r in self.rows)
        page='<!doctype html><meta charset="utf-8"><title>XZY01 console</title><h1>控制台结果</h1><p>None=未报告；固定测试与综合分开；不代表形式等价或时序签核。</p><table border="1"><tr>'+''.join('<th>'+k+'</th>' for k in headers)+'</tr>'+body+'</table><h2>已有学校结果（只读）</h2><pre>'+html.escape(json.dumps(b.school_history(),ensure_ascii=False,indent=2))+'</pre>'
        path.write_text(page,encoding='utf-8');os.startfile(path)
    def school_results(self):self.show(self.schooltext,b.school_history())
    def pack(self):
        row=self.selected();tool=self.tool.get()
        shared=filedialog.askdirectory(title='选择已映射到学校的共享目录')
        if not shared:return
        profile=None;sdc=None
        if tool in ('dc','genus'):
            cfg=filedialog.askopenfilename(title='选择已审核的综合配置 JSON')
            if not cfg:return
            profile=b.read(cfg)['tools'][tool]
            sdc=filedialog.askopenfilename(title='选择匹配当前槽的已审核 SDC')
            if not sdc:return
            b.require(messagebox.askyesno('确认约束','已核对所选 SDC、库、工艺角与当前槽匹配？'),'尚未审核约束')
            profile=dict(profile,constraints_reviewed=True)
        self.school_record=school.pack(row,tool,shared,profile,sdc)
        self.show(self.schooltext,dict(self.school_record,note='仅打包；没有执行学校工具。'))
    def copy_command(self,action='run'):
        b.require(self.school_record is not None,'请先打包一个案例')
        command=school.command(self.school_record,action)
        self.root.clipboard_clear();self.root.clipboard_append(command)
        self.show(self.schooltext,{'manual_command':command,'note':'学校终端人工运行一次；此按钮只复制。'})
    def load_school_record(self):
        p=filedialog.askopenfilename(initialdir=str(b.STATE/'school'),title='选择本机打包记录（或已准备的 vcs/xcelium/dc/genus.json）')
        if not p:return
        record=b.read(p)
        b.require(all(k in record for k in ('key','local','shared','manifest_sha256','files')),'请选择打包记录，不能选择结果或配置文件')
        manifest=Path(record['local'])/'console-manifest.json'
        b.require(b.sha(manifest)==record['manifest_sha256'] and b.read(manifest)['key']==record['key'],'本机打包记录与清单不符')
        self.school_record=record
        self.show(self.schooltext,dict(record,note='载入已有包，未重新打包、未执行工具。'))
    def collect(self):
        if self.school_record is None:
            self.load_school_record()
            if self.school_record is None:return
        p=filedialog.askopenfilename(title='选择共享 inbox 中 console-return.json',initialdir=str(Path(self.school_record['shared'])/'inbox'/self.school_record['key']),initialfile='console-return.json')
        if p:self.show(self.schooltext,school.collect(self.school_record,p))
    def legacy(self):
        subprocess.Popen([sys.executable,str(b.ROOT/'lab_gui.py')],cwd=b.ROOT,creationflags=subprocess.CREATE_NO_WINDOW)
    def close(self):
        if self.busy:messagebox.showinfo('处理中','等待任务结束后关闭，避免未知结果。');return
        self.key.set('');self.root.destroy()

if __name__=='__main__':
    root=tk.Tk();Console(root);root.mainloop()
