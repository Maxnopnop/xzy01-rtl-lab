"""Native local window for the existing CLI; no HTTP server or model calls on launch."""
import csv
import ctypes
import datetime
import hashlib
import io
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import uuid
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText

import batch
import model_platform
import ece_synthesis
from ece_synth_common import TOOLS as SYNTH_TOOLS, template as synthesis_template, validate_profile as validate_synthesis_profile

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / 'config.local.models.csv'
SCHOOL_COMMAND = 'bash -c \'find "$HOME/tsclient" -maxdepth 6 -type f -path "*/ECE-Transfer/ece_menu.sh" -exec bash {} \\; -quit\''
MODES = ('完整提示词 · 仅生成', '完整提示词 · 仿真＋综合＋学校打包', '原有 dev10 提示词 · 仿真＋综合＋学校打包')


def clipboard_text(window):
    """Read CF_UNICODETEXT directly on Windows, preserving original CR/LF."""
    if os.name != 'nt':
        return window.clipboard_get()
    user = ctypes.WinDLL('user32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    user.GetClipboardData.argtypes = [ctypes.c_uint]
    user.GetClipboardData.restype = ctypes.c_void_p
    kernel.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel.GlobalLock.restype = ctypes.c_void_p
    kernel.GlobalUnlock.argtypes = [ctypes.c_void_p]
    if not user.OpenClipboard(None):
        raise ValueError('剪贴板正在被其他程序使用，请再按一次粘贴。')
    try:
        handle = user.GetClipboardData(13)  # CF_UNICODETEXT
        if not handle:
            raise ValueError('剪贴板里没有文字。')
        pointer = kernel.GlobalLock(handle)
        if not pointer:
            raise ValueError('读取剪贴板失败。')
        try:
            return ctypes.wstring_at(pointer)
        finally:
            kernel.GlobalUnlock(handle)
    finally:
        user.CloseClipboard()


class OriginalPrompt:
    def __init__(self):
        self.data = b''

    def set(self, data):
        data.decode('utf-8')
        if not data or len(data) > 1024 * 1024:
            raise ValueError('提示词需要是非空 UTF-8 文本，最大 1 MiB。')
        self.data = bytes(data)

    def save(self, path):
        if not self.data:
            raise ValueError('请先粘贴完整提示词或导入 UTF-8 文件。')
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(self.data)
        assert path.read_bytes() == self.data


def csv_rows(text):
    reader = csv.DictReader(io.StringIO(text, newline=''))
    if reader.fieldnames != model_platform.FIELDS:
        raise ValueError('CSV 表头必须是：' + ','.join(model_platform.FIELDS))
    rows = list(reader)
    if not rows or any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError('CSV 行不完整。密钥本身不要放进 CSV。')
    # Reuse authoritative validation without touching the user's saved config.
    with tempfile.TemporaryDirectory() as directory:
        file = Path(directory) / 'profiles.csv'
        file.write_text(text, encoding='utf-8', newline='')
        try:
            model_platform.profiles(file)
        except ValueError as exc:
            if str(exc) != 'Enable at least one profile in CSV':
                raise
    return rows


def csv_text(rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=model_platform.FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def build_command(mode, run, prompt_dir, task, samples, cap, profile_count, synthesis='auto'):
    if mode not in range(3) or samples < 1 or cap < 1:
        raise ValueError('次数和预算必须是正整数。')
    valid = {s['id'] for s in batch.manifest('dev10')}
    if mode != 0 and task not in valid | ({'all'} if mode == 2 else set()):
        raise ValueError('原文仿真模式必须选择一个匹配的固定测试任务。')
    task_count = len(valid) if mode == 2 and task == 'all' else 1
    calls = profile_count * samples * task_count
    if calls > cap:
        raise ValueError('计划 %d 次调用，超过预算 %d。请减少模型、任务或重复数。' % (calls, cap))
    if mode == 0:
        args = ['generate', '--prompt-file', str(prompt_dir / 'full_prompt.txt')]
    else:
        args = ['local', '--tasks', task, '--synthesis', synthesis]
        if mode == 1:
            args += ['--prompt-dir', str(prompt_dir)]
    args += ['--profiles', str(CONFIG), '--run-dir', str(run), '--samples', str(samples), '--max-total-calls', str(cap)]
    return args, calls


class LabWindow:
    def __init__(self, window):
        self.window = window
        self.prompt = OriginalPrompt()
        self.keys = {}
        self.events = queue.Queue()
        self.busy = False
        self.proc = None
        self.last_run = None
        window.title('XZY01 RTL Lab — 本机实验控制台')
        window.geometry('1080x800')
        window.minsize(860, 680)
        style = ttk.Style(window)
        if 'vista' in style.theme_names():
            style.theme_use('vista')
        style.configure('TButton', padding=(10, 5))
        style.configure('Title.TLabel', font=('Microsoft YaHei UI', 18, 'bold'))
        frame = ttk.Frame(window, padding=16)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='XZY01 · RTL 实验控制台', style='Title.TLabel').pack(anchor='w')
        ttk.Label(frame, text='配置模型 → 粘贴原文 → 本机验证 → 学校单案例复核', padding=(0, 5)).pack(anchor='w')
        self.tabs = ttk.Notebook(frame)
        self.tabs.pack(fill='both', expand=True, pady=8)
        self.models_tab = ttk.Frame(self.tabs, padding=12)
        self.run_tab = ttk.Frame(self.tabs, padding=12)
        self.results_tab = ttk.Frame(self.tabs, padding=12)
        self.synth_tab = ttk.Frame(self.tabs, padding=12)
        for page, name in ((self.models_tab, '1  模型配置'), (self.run_tab, '2  提示词与运行'), (self.results_tab, '3  结果与学校传输'), (self.synth_tab, '4  学校综合 DC / Genus')):
            self.tabs.add(page, text=name)
        self.setup_models()
        self.setup_run()
        self.setup_results()
        self.setup_synthesis()
        self.status = tk.StringVar(value='就绪 · 打开窗口不会调用 API')
        ttk.Label(frame, textvariable=self.status).pack(anchor='w', pady=(6, 3))
        self.log = ScrolledText(frame, height=7, font=('Consolas', 10), state='disabled')
        self.log.pack(fill='x')
        window.protocol('WM_DELETE_WINDOW', self.close)
        window.after(100, self.poll)

    def guarded(self, callback):
        def wrapped():
            try:
                if self.busy:
                    raise ValueError('当前任务正在执行，请等结束后再操作。')
                return callback()
            except Exception as exc:
                self.error(exc)
        return wrapped

    def button(self, parent, label, callback):
        button = ttk.Button(parent, text=label, command=self.guarded(callback))
        button.pack(side='left', padx=(0, 7), pady=4)
        return button

    def setup_models(self):
        box = ttk.LabelFrame(self.models_tab, text='添加或更新一行模型', padding=10)
        box.pack(fill='x')
        self.fields = {}
        for index, (name, title, default) in enumerate([
            ('id', '配置名称', 'vendor_a'), ('base_url', 'base_url', 'https://api.example.com/v1'),
            ('model', '实际模型 ID', ''), ('api_key_env', '密钥变量名称', 'VENDOR_A_API_KEY')]):
            row, col = divmod(index, 2)
            ttk.Label(box, text=title).grid(row=row, column=col * 2, sticky='w', padx=4, pady=5)
            value = tk.StringVar(value=default)
            self.fields[name] = value
            ttk.Entry(box, textvariable=value, width=34).grid(row=row, column=col * 2 + 1, sticky='ew', padx=4)
            box.columnconfigure(col * 2 + 1, weight=1)
        bar = ttk.Frame(self.models_tab)
        bar.pack(fill='x')
        self.button(bar, '添加 / 更新为启用', self.add_model)
        self.button(bar, '保存配置', self.save_config)
        self.button(bar, '填写 API 密钥（隐藏）', self.enter_keys)
        self.button(bar, '检查配置（不联网）', self.check_config)
        ttk.Label(self.models_tab, text='也可在下方批量粘贴 CSV；enabled=true 才参与运行。protocol 当前为 chat_completions。').pack(anchor='w', pady=5)
        self.csv = ScrolledText(self.models_tab, height=9, wrap='none', font=('Consolas', 10))
        self.csv.pack(fill='both', expand=True)
        if CONFIG.exists():
            text = CONFIG.read_text(encoding='utf-8-sig')
        else:
            text = csv_text([dict(id='vendor_a', enabled='false', protocol='chat_completions', base_url='https://api.example.com/v1', model='REPLACE_MODEL_ID', api_key_env='VENDOR_A_API_KEY')])
        self.csv.insert('1.0', text)
        ttk.Label(self.models_tab, text='密钥只留在当前窗口内存中。关闭窗口后需重新填写；CSV 中只保存环境变量名称。').pack(anchor='w', pady=8)

    def add_model(self):
        rows = csv_rows(self.csv.get('1.0', 'end-1c'))
        row = {k: v.get().strip() for k, v in self.fields.items()}
        row.update(enabled='true', protocol='chat_completions')
        rows = [r for r in rows if r['id'] != row['id']] + [row]
        text = csv_text(rows)
        csv_rows(text)
        self.csv.delete('1.0', 'end')
        self.csv.insert('1.0', text)
        self.status.set('模型行已更新；按“保存配置”或开始运行时保存。')

    def save_config(self):
        text = self.csv.get('1.0', 'end-1c')
        csv_rows(text)
        temp = CONFIG.with_name(CONFIG.name + '.tmp')
        temp.write_text(text, encoding='utf-8', newline='')
        temp.replace(CONFIG)
        self.status.set('本机模型配置已保存；没有调用 API。')

    def enter_keys(self):
        self.save_config()
        profiles = model_platform.profiles(CONFIG)
        for name in dict.fromkeys(p['api_key_env'] for p in profiles):
            value = simpledialog.askstring('API 密钥', name + '\n输入密钥（留空保留已有值）：', show='*', parent=self.window)
            if value:
                self.keys[name] = value
        self.status.set('密钥已保存在当前窗口内存；没有写入磁盘。')

    def check_config(self):
        self.save_config()
        self.start(['check', '--profiles', str(CONFIG), '--tasks', 've_count10'], script='model_platform.py')

    def setup_run(self):
        self.mode = tk.StringVar(value=MODES[0])
        self.task = tk.StringVar(value='ve_count10')
        self.samples = tk.StringVar(value='1')
        self.cap = tk.StringVar(value='2')
        self.synthesis = tk.StringVar(value='auto')
        row = ttk.Frame(self.run_tab)
        row.pack(fill='x')
        ttk.Label(row, text='运行方式').pack(side='left')
        ttk.Combobox(row, textvariable=self.mode, values=MODES, state='readonly', width=43).pack(side='left', padx=6)
        ttk.Label(row, text='固定任务').pack(side='left')
        ttk.Combobox(row, textvariable=self.task, values=['all'] + [s['id'] for s in batch.manifest('dev10')], state='readonly', width=20).pack(side='left', padx=6)
        row = ttk.Frame(self.run_tab)
        row.pack(fill='x', pady=8)
        for title, value in [('每模型重复数', self.samples), ('总调用上限', self.cap)]:
            ttk.Label(row, text=title).pack(side='left')
            ttk.Spinbox(row, from_=1, to=10000, textvariable=value, width=7).pack(side='left', padx=(6, 18))
        ttk.Label(row, text='综合').pack(side='left')
        ttk.Combobox(row, textvariable=self.synthesis, values=['auto', 'native', 'wsl', 'none'], state='readonly', width=8).pack(side='left', padx=6)
        bar = ttk.Frame(self.run_tab)
        bar.pack(fill='x')
        self.button(bar, '粘贴完整提示词', self.paste_prompt)
        self.button(bar, '导入 UTF-8 文件', self.import_prompt)
        self.button(bar, '查看预算（不调用）', self.preview)
        self.button(bar, '开始运行（消耗 API 额度）', self.run)
        self.prompt_label = tk.StringVar(value='尚未输入提示词。原文模式只发送一条 user 消息。')
        ttk.Label(self.run_tab, textvariable=self.prompt_label).pack(anchor='w', pady=6)
        self.prompt_view = ScrolledText(self.run_tab, height=10, font=('Microsoft YaHei UI', 10), wrap='word', state='disabled')
        self.prompt_view.pack(fill='both', expand=True)
        self.prompt_view.bind('<Control-v>', lambda event: (self.guarded(self.paste_prompt)(), 'break')[1])
        ttk.Label(self.run_tab, text='预览只读；整段重新粘贴可替换原文。任意设计选“仅生成”；自动仿真须与固定任务接口和行为匹配。').pack(anchor='w', pady=7)

    def set_prompt(self, data):
        self.prompt.set(data)
        self.prompt_view.configure(state='normal')
        self.prompt_view.delete('1.0', 'end')
        # Display normalization cannot reach the authoritative byte buffer.
        self.prompt_view.insert('1.0', data.decode('utf-8').replace('\r\n', '\n'))
        self.prompt_view.configure(state='disabled')
        self.prompt_label.set('%d UTF-8 字节 · SHA-256 %s… · 原文已锁定' % (len(data), hashlib.sha256(data).hexdigest()[:16]))

    def paste_prompt(self):
        self.set_prompt(clipboard_text(self.window).encode('utf-8'))

    def import_prompt(self):
        path = filedialog.askopenfilename(parent=self.window, title='选择完整 UTF-8 提示词', filetypes=[('文本', '*.txt'), ('所有文件', '*')])
        if path:
            self.set_prompt(Path(path).read_bytes())

    def options(self):
        self.save_config()
        profiles = model_platform.profiles(CONFIG)
        mode = MODES.index(self.mode.get())
        run = ROOT / 'runs' / ('gui-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6])
        prompt_dir = ROOT / 'config.local.gui-prompts' / run.name
        args, calls = build_command(mode, run, prompt_dir, self.task.get(), int(self.samples.get()), int(self.cap.get()), len(profiles), self.synthesis.get())
        if mode != 2 and not self.prompt.data:
            raise ValueError('请先粘贴或导入完整提示词。')
        return profiles, mode, run, prompt_dir, args, calls

    def preview(self):
        profiles, mode, run, prompt_dir, args, calls = self.options()
        names = ', '.join(p['id'] for p in profiles)
        self.status.set('计划 %d 次调用 / 上限 %s；模型：%s。预览未调用 API。' % (calls, self.cap.get(), names))

    def run(self):
        profiles, mode, run, prompt_dir, args, calls = self.options()
        for name in dict.fromkeys(p['api_key_env'] for p in profiles):
            if not self.keys.get(name) and not os.environ.get(name):
                value = simpledialog.askstring('填写本次所需密钥', name, show='*', parent=self.window)
                if not value:
                    raise ValueError('未提供密钥，尚未开始调用。')
                self.keys[name] = value
        if mode != 2:
            self.prompt.save(prompt_dir / ('full_prompt.txt' if mode == 0 else self.task.get() + '.txt'))
        self.last_run = run
        self.start(args, description='计划 %d 次调用 · %s' % (calls, run.name))

    def setup_results(self):
        for caption, actions in [
            ('本机检查与结果', [('检查本机工具', lambda: self.start(['doctor'])), ('更新汇总报告', lambda: self.start(['report'])), ('打开汇总报告', lambda: self.open_path(ROOT / 'workflow/lab-report.html')), ('打开本次结果', self.open_last)]),
            ('学校共享文件夹（每次人工选择一个案例）', [('打开共享目录', lambda: self.open_path(Path.home() / 'Documents/FYP/ECE-Transfer')), ('复制学校运行命令', self.copy_school), ('收取共享结果', lambda: self.start(['collect']))]),
            ('GitHub 传输', [('发布学校包到 GitHub', lambda: self.start(['export-git', '--push'])), ('收取 Git 和共享结果', lambda: self.start(['collect', '--git']))]),
            ('文件与备份', [('打开项目目录', lambda: self.open_path(ROOT)), ('打开操作指南', lambda: self.open_path(ROOT / 'FYP_ONE_COMMAND.md')), ('备份本地实验', self.backup)])]:
            group = ttk.LabelFrame(self.results_tab, text=caption, padding=8)
            group.pack(fill='x', pady=6)
            for title, action in actions:
                self.button(group, title, action)
        ttk.Label(self.results_tab, text='学校：先登录 Horizon / ECE LAB7，再粘贴复制的命令。\nGit 按钮使用本机已有认证；窗口内不交互输入 Git 密码。登录问题见操作指南。', justify='left').pack(anchor='w', pady=8)

    def open_path(self, path):
        if not path.exists():
            raise ValueError('尚未生成：' + str(path))
        if os.name == 'nt':
            os.startfile(str(path))
        else:
            subprocess.Popen(['xdg-open', str(path)])

    def setup_synthesis(self):
        self.synth_settings = ece_synthesis.read(ece_synthesis.CONFIG) if ece_synthesis.CONFIG.exists() else synthesis_template()
        self.synth_active = 'dc'
        self.synth_tool = tk.StringVar(value='dc')
        self.synth_corner = tk.StringVar()
        self.synth_sdc = tk.StringVar()
        self.synth_reviewed = tk.BooleanVar(value=False)
        self.synth_timeout = tk.StringVar(value='600')
        top = ttk.Frame(self.synth_tab)
        top.pack(fill='x')
        ttk.Label(top, text='学校综合工具').pack(side='left')
        selector = ttk.Combobox(top, textvariable=self.synth_tool, values=['dc', 'genus'], state='readonly', width=10)
        selector.pack(side='left', padx=8)
        selector.bind('<<ComboboxSelected>>', lambda event: self.guarded(self.switch_synthesis)())
        self.synth_info = tk.StringVar()
        ttk.Label(top, textvariable=self.synth_info).pack(side='left')
        ttk.Label(self.synth_tab, text='学校标准单元库绝对路径（每行一个；DC: .db / Genus: .lib 或 .lib.gz；库文件不传到本机）').pack(anchor='w', pady=(8, 3))
        self.synth_libs = ScrolledText(self.synth_tab, height=3, font=('Consolas', 10))
        self.synth_libs.pack(fill='x')
        row = ttk.Frame(self.synth_tab)
        row.pack(fill='x', pady=5)
        ttk.Label(row, text='工艺角标签').pack(side='left')
        ttk.Entry(row, textvariable=self.synth_corner, width=28).pack(side='left', padx=6)
        ttk.Label(row, text='最长秒数').pack(side='left')
        ttk.Spinbox(row, from_=10, to=3600, textvariable=self.synth_timeout, width=8).pack(side='left', padx=6)
        row = ttk.Frame(self.synth_tab)
        row.pack(fill='x')
        ttk.Label(row, text='本机 SDC 文件').pack(side='left')
        ttk.Entry(row, textvariable=self.synth_sdc).pack(side='left', fill='x', expand=True, padx=6)
        self.button(row, '选择 SDC', self.choose_sdc)
        ttk.Checkbutton(self.synth_tab, text='我已核对该 SDC 与所选设计、库和工艺角匹配', variable=self.synth_reviewed).pack(anchor='w', pady=4)
        row = ttk.Frame(self.synth_tab)
        row.pack(fill='x')
        self.button(row, '保存综合配置', self.save_synthesis)
        self.button(row, '检查配置（不启动工具）', self.check_synthesis)
        self.button(row, '查看启动验证记录', lambda: self.open_path(ROOT / 'ECE_SYNTHESIS_STARTUP.md'))
        self.button(row, '复制查库命令', self.copy_library_query)
        ttk.Label(self.synth_tab, text='选择已有原始 RTL 样本；每个包只包含一个设计和一个综合工具：').pack(anchor='w', pady=(8, 2))
        self.synth_selection = tk.StringVar()
        self.synth_cases = ttk.Combobox(self.synth_tab, textvariable=self.synth_selection, state='readonly', width=80)
        self.synth_cases.pack(fill='x')
        self.synth_cases.bind('<<ComboboxSelected>>', lambda event: self.synth_reviewed.set(False))
        row = ttk.Frame(self.synth_tab)
        row.pack(fill='x')
        self.button(row, '刷新样本', self.refresh_synthesis)
        self.button(row, '生成单案例学校包', self.pack_synthesis)
        self.button(row, '复制学校综合命令', self.copy_synthesis_command)
        self.button(row, '收取综合结果', lambda: self.start(['collect'], script='ece_synthesis.py'))
        self.button(row, '综合报告', lambda: self.open_path(ece_synthesis.STATE / 'report.html'))
        ttk.Label(self.synth_tab, text='当前只有工具启动证据。缺少库或已审核约束时会阻止实际综合；完成输出后仍需审阅报告。\n此页通过 ECE-Synthesis 共享目录传输。Yosys 及 VCS/Xcelium 的既有结果保持独立。', justify='left').pack(anchor='w', pady=5)
        self.load_synthesis()
        self.refresh_synthesis()

    def capture_synthesis(self):
        profile = dict(libraries=[line.strip() for line in self.synth_libs.get('1.0', 'end-1c').splitlines() if line.strip()],
            corner=self.synth_corner.get(), sdc_file=self.synth_sdc.get(),
            constraints_reviewed=self.synth_reviewed.get(), timeout_seconds=int(self.synth_timeout.get()))
        missing = validate_synthesis_profile(self.synth_active, profile)
        self.synth_settings['tools'][self.synth_active] = profile
        return missing

    def load_synthesis(self):
        tool = self.synth_active
        profile = self.synth_settings['tools'][tool]
        self.synth_libs.delete('1.0', 'end')
        self.synth_libs.insert('1.0', '\n'.join(profile['libraries']))
        self.synth_corner.set(profile['corner'])
        self.synth_sdc.set(profile['sdc_file'])
        # A reopened window/tool may select a different design; review again.
        self.synth_reviewed.set(False)
        self.synth_timeout.set(str(profile['timeout_seconds']))
        self.synth_info.set(SYNTH_TOOLS[tool]['name'] + ' · ' + SYNTH_TOOLS[tool]['version'] + '（启动已验证）')

    def switch_synthesis(self):
        try:
            self.capture_synthesis()
        except Exception:
            self.synth_tool.set(self.synth_active)
            raise
        self.synth_active = self.synth_tool.get()
        self.load_synthesis()

    def choose_sdc(self):
        path = filedialog.askopenfilename(parent=self.window, title='选择你已审核的 SDC 约束', filetypes=[('SDC', '*.sdc'), ('所有文件', '*')])
        if path:
            self.synth_sdc.set(path)
            self.synth_reviewed.set(False)

    def save_synthesis(self):
        missing = self.capture_synthesis()
        ece_synthesis.save(ece_synthesis.CONFIG, self.synth_settings)
        self.status.set('综合配置已保存；' + ('缺少：' + ', '.join(missing) if missing else '需在学校检查库可读性与许可证。'))

    def check_synthesis(self):
        self.save_synthesis()
        self.start(['check'], script='ece_synthesis.py')

    def refresh_synthesis(self):
        self.synth_options = {str(Path(r['run_dir']).relative_to(ROOT)) + ' / ' + r['job_id'] + ' [' + r['status'] + ']': r for r in ece_synthesis.candidates()}
        self.synth_cases.configure(values=list(self.synth_options))
        if self.synth_selection.get() not in self.synth_options:
            self.synth_selection.set(next(iter(self.synth_options), ''))

    def pack_synthesis(self):
        self.save_synthesis()
        selected = self.synth_options.get(self.synth_selection.get())
        if not selected:
            raise ValueError('请先选择一个已经提取 RTL 的实验样本。')
        self.start(['pack', '--run-dir', selected['run_dir'], '--job', selected['job_id'], '--tool', self.synth_active], script='ece_synthesis.py')

    def copy_synthesis_command(self):
        command = 'bash -c \'find "$HOME/tsclient" -maxdepth 6 -type f -path "*/ECE-Synthesis/ece_synth_menu.sh" -exec bash {} \\; -quit\''
        self.window.clipboard_clear()
        self.window.clipboard_append(command)
        self.status.set('学校综合命令已复制；只会运行一个人工选择的案例，缺库时不会启动工具。')

    def copy_library_query(self):
        command = 'bash -c \'timeout 30s find -L /usr/eelocal /staff/ee/dept/public -maxdepth 7 -type f \\( -iname "*.db" -o -iname "*.lib" -o -iname "*.lib.gz" \\) -readable -print 2>/dev/null | head -n 100\''
        self.window.clipboard_clear()
        self.window.clipboard_append(command)
        self.status.set('只读查库命令已复制；在学校终端执行，最多30秒。')

    def open_last(self):
        if not self.last_run:
            raise ValueError('本次窗口还没有创建实验，可先打开项目 runs 目录。')
        self.open_path(self.last_run)

    def copy_school(self):
        self.window.clipboard_clear()
        self.window.clipboard_append(SCHOOL_COMMAND)
        self.status.set('学校单案例命令已复制；在 ECE Linux 终端粘贴即可。')

    def backup(self):
        file = filedialog.asksaveasfilename(parent=self.window, title='保存本地实验备份', initialfile='fyp-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.zip', defaultextension='.zip')
        if file:
            self.start(['backup', '--output', file])

    def redact(self, text):
        for secret in self.keys.values():
            if secret:
                text = text.replace(secret, '[REDACTED]')
        return text

    def error(self, exc):
        messagebox.showerror('暂未执行', self.redact(str(exc)), parent=self.window)

    def start(self, args, script='lab_flow.py', description='执行中'):
        if self.busy:
            raise ValueError('已有任务正在运行。')
        self.busy = True
        self.status.set(description)
        env = os.environ.copy()
        env.update(self.keys, PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1', GIT_TERMINAL_PROMPT='0')
        def work():
            try:
                options = dict(creationflags=subprocess.CREATE_NO_WINDOW) if os.name == 'nt' else {}
                self.proc = subprocess.Popen([sys.executable, '-u', str(ROOT / script)] + args, cwd=ROOT,
                    env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    encoding='utf-8', errors='replace', **options)
                with self.proc.stdout:
                    for line in self.proc.stdout:
                        self.events.put(('log', self.redact(line)))
                self.events.put(('done', self.proc.wait()))
            except Exception as exc:
                self.events.put(('log', self.redact(str(exc)) + '\n'))
                self.events.put(('done', 2))
        threading.Thread(target=work, daemon=True).start()

    def poll(self):
        for _ in range(100):
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == 'done':
                self.busy = False
                self.proc = None
                self.status.set('任务结束 · 退出码 %s。0=成功；非0请查看日志/结果；不自动重试调用。' % value)
            else:
                self.log.configure(state='normal')
                self.log.insert('end', value)
                if int(self.log.index('end-1c').split('.')[0]) > 1200:
                    self.log.delete('1.0', '200.0')
                self.log.see('end')
                self.log.configure(state='disabled')
        self.window.after(100, self.poll)

    def close(self):
        if self.busy:
            messagebox.showinfo('任务正在运行', '请等待当前任务结束后关闭窗口，避免产生结果不明的 API 调用。', parent=self.window)
            return
        self.keys.clear()
        self.window.destroy()


if __name__ == '__main__':
    os.chdir(ROOT)
    root = tk.Tk()
    app = LabWindow(root)
    if '--synthesis-tab' in sys.argv:
        app.tabs.select(app.synth_tab)
        root.title('XZY01 RTL Lab — DC / Genus 学校综合')
    root.mainloop()
