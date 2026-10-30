"""New R6 streaming version; no auth probe output is persisted."""
import os,sys,subprocess,urllib.request
from pathlib import Path
import stream_process as sp
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
sys.path.insert(0,str(ROOT))
import rtl_lab as lab
from codex_adapter import find_codex
def generate_text(args,folder,prompt):
    folder=Path(folder)
    if (folder/'reservation.json').exists():raise lab.LabError('UNKNOWN_INTERRUPTED','reservation','Reserved request cannot be resent')
    exe=find_codex(args.codex_executable);env=lab.clean_env()
    for key,name in [('http','HTTP_PROXY'),('https','HTTPS_PROXY'),('all','ALL_PROXY'),('no','NO_PROXY')]:
        value=urllib.request.getproxies().get(key)
        if value:env[name]=value
    for name in ['APPDATA','LOCALAPPDATA','CODEX_HOME']:
        if os.environ.get(name):env[name]=os.environ[name]
    # Trusted local probes held in memory. Neither auth stdout nor stderr saved.
    version=subprocess.run([exe,'--version'],capture_output=True,timeout=15,env=env)
    auth=subprocess.run([exe,'login','status'],capture_output=True,timeout=15,env=env)
    if version.returncode or auth.returncode or b'Logged in using ChatGPT' not in auth.stdout+auth.stderr:
        raise lab.LabError('ENV_ERROR','local_preflight','Local version/login preflight failed; auth output not retained')
    folder.mkdir(parents=True,exist_ok=True);working=folder/'generation_workspace';working.mkdir()
    output=folder/'model_output.raw.txt'
    command=[exe,'exec','--ignore-user-config','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--model',args.model,'--json','--color','never',
             '-c','model_provider="openai"','-c','forced_login_method="chatgpt"','-c',f'model_reasoning_effort="{args.codex_reasoning}"',
             '-c','approval_policy="never"','-c','project_doc_max_bytes=0','-c','web_search="disabled"']
    for feature in ['shell_tool','multi_agent','apps','plugins','remote_plugin','hooks','memories','image_generation','computer_use','browser_use','in_app_browser','skill_search']:command.extend(['--disable',feature])
    command.extend(['--output-last-message',str(output),'-'])
    r=sp.capture(command,folder,prompt.encode(),args.model,timeout=args.api_timeout,env=env,cwd=working,
                 context=dict(adapter_sha256=sp.digest(Path(__file__).read_bytes()),process_sha256=sp.digest(Path(sp.__file__).read_bytes()),executable_sha256=sp.digest(Path(exe).read_bytes()),
                              cli_version=version.stdout.decode(errors='replace').strip(),reasoning=args.codex_reasoning,final_output_name='model_output.raw.txt',auth='ChatGPT locally checked; raw auth not saved',max_output_tokens=None,temperature=None,seed=None,proxy_names=sorted(k for k in env if k.endswith('_PROXY'))))
    if r['status']!='GENERATED':raise lab.LabError('UNKNOWN_INTERRUPTED','stream_capture',r.get('boundary',r['status']))
    if not output.is_file() or output.read_bytes()!=r['response'].encode():raise lab.LabError('UNKNOWN_INTERRUPTED','final_boundary','Final output/event mismatch')
    # Fields missing from provider events remain unknown rather than invented.
    return r['response'],dict(usage=r['usage'],generation_seconds=r['exit']['elapsed_seconds'],codex_thread_id=r['thread_id'],model_called=True,
                              response_model=None,model_identity_basis='Requested CLI model; backend snapshot not exposed',source='STREAM_CAPTURE_V1',tools_used=False)
