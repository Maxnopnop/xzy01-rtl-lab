"""Real Windows subprocess transport, fake CLI receiver; no model calls or network."""
import sys,json,uuid,subprocess,importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];V2=BASE.parent/'r3-runner-v2'
sys.path[:0]=[str(BASE),str(ROOT),str(BASE.parent/'r3')]
import runner,cli_adapter as new,stdin_process,batch,rtl_lab as lab,codex_network_adapter as old
RUN=BASE/'runs/transport-v1';WORKER=BASE/'cli_fixture.py'
REAL_PROCESS=lab.run_process
ARGS=SimpleNamespace(codex_executable=sys.executable,model='OFFLINE_FIXTURE',codex_reasoning='low',api_timeout=10)

def historical():
    spec=importlib.util.spec_from_file_location('prior_acceptance',V2/'acceptance.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result=module.preserved()
    for p in V2.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:result[str(p.relative_to(ROOT))]=lab.digest(p.read_bytes())
    for p in [BASE.parent/'v2-regression-initial.log',BASE.parent/'v2-loopback-regression/summary.json',BASE.parent/'v2-loopback-regression/unittest.log']:
        result[str(p.relative_to(ROOT))]=lab.digest(p.read_bytes())
    return result

def command_route(command):
    assert Path(command[0]).resolve()==Path(sys.executable).resolve(),'Real CLI execution forbidden'
    return [sys.executable,str(WORKER),*command[1:]]

def fixture_run(command,cwd,timeout,env=None):
    return REAL_PROCESS(command_route(command),cwd,timeout,lab.clean_env())

def fixture_stdin(command,cwd,timeout,env,path):
    return stdin_process.run_process_stdin(command_route(command),cwd,timeout,lab.clean_env(),path)

def configure(folder,mode='normal'):
    folder.mkdir(parents=True,exist_ok=True)
    nonce=uuid.uuid4().hex
    batch.atomic(folder/'fixture-control.json',dict(mode=mode,nonce=nonce))
    return nonce

def receive(folder,prompt,nonce):
    expected=prompt.encode('utf-8');receipt=batch.read(folder/'receipt.json')
    assert receipt['nonce']==nonce and receipt['source']=='stdin'
    assert receipt['bytes']==len(expected) and receipt['sha256']==lab.digest(expected)
    assert (folder/'received-prompt.bin').read_bytes()==expected==(folder/'codex_prompt.txt').read_bytes()
    assert receipt['argv'][-1]=='-' and prompt not in receipt['argv']
    request=batch.read(folder/'codex_request.json')
    assert request['prompt_sha256']==lab.digest(expected) and request['prompt_bytes']==len(expected)
    result=batch.read(folder/'codex.json')
    assert result['returncode']==0 and not result['timeout'] and not result['output_limit']
    return dict(bytes=len(expected),sha256=lab.digest(expected),nonce=nonce,
                command_utf16_units=len(subprocess.list2cmdline(result['command']).encode('utf-16-le'))//2)

def main():
    assert sys.platform=='win32' and not RUN.exists()
    RUN.mkdir(parents=True);before=historical();batch.atomic(RUN/'preserved-before.json',before)
    sources=runner.hashes();batch.atomic(RUN/'source-lock.json',sources)
    # Only real executable commands are local help/version, never exec generation.
    exe=old.find_codex(None)
    for label,cmd in [('help',[exe,'exec','--help']),('version',[exe,'--version'])]:
        result=REAL_PROCESS(cmd,RUN,15,lab.clean_env());lab.save_process(RUN,'real-cli-'+label,result)
        assert result['returncode']==0 and not result['timeout']
        if label=='help':assert 'instructions are read from stdin' in result['stdout']
    batch.atomic(RUN/'real-cli-identity.json',dict(sha256=lab.digest(Path(exe).read_bytes()),local_commands_only=True))
    jobs=[]
    flow=V2/'runs/acceptance-v1/full-flow'
    plan=batch.read(V2/'runs/acceptance-v1/fixture-plan.json')
    for job in plan['jobs']:
        if job['role']=='branch':
            prompt=(flow/'jobs'/job['id']/'call/exact-prompt.txt').read_bytes().decode('utf-8')
            jobs.append((job,prompt))
    assert len(jobs)==16
    baseline=[];newrows=[]
    with patch.object(lab,'run_process',side_effect=fixture_run),patch.object(old,'find_codex',return_value=sys.executable),patch.object(new,'find_codex',return_value=sys.executable),patch.object(new,'run_process_stdin',side_effect=fixture_stdin),patch.object(old,'model_network_env',side_effect=lab.clean_env),patch.object(new,'model_network_env',side_effect=lab.clean_env):
        for job,prompt in jobs:
            folder=RUN/'original-argv'/job['id'];nonce=configure(folder)
            try:
                old.generate_text(ARGS,folder,prompt)
                receipt=batch.read(folder/'receipt.json')
                assert (folder/'received-prompt.bin').read_bytes()==prompt.encode('utf-8')
                outcome=dict(status='RECEIVED',receipt_sha256=receipt['sha256'])
            except OSError as exc:
                assert exc.winerror==206,(job['id'],exc)
                assert not (folder/'receipt.json').exists()
                outcome=dict(status='CREATEPROCESS_ERROR',winerror=exc.winerror,message=str(exc))
            outcome.update(id=job['id'],prompt_bytes=len(prompt.encode('utf-8')))
            batch.atomic(folder/'transport-result.json',outcome);baseline.append(outcome)
            # Exercise new runner.generate -> adapter -> real child, not a fake generate callback.
            folder=RUN/'new-stdin/jobs'/job['id']/'call';nonce=configure(folder)
            result=runner.generate(RUN/'new-stdin',job,dict(model='OFFLINE_FIXTURE',reasoning='low',api_timeout=10,max_calls=24),prompt)
            assert result['status']=='GENERATED' and result['tools_used'] is False
            record=receive(folder,prompt,nonce);record['id']=job['id'];newrows.append(record)
        # Mixed line endings and shell-sensitive Unicode are data, with no shell execution.
        seed='\r\nLF\n中文🙂 "quote" \\backslash\\ $() `ticks`\r\n'
        mixed=(seed*((1024*1024)//len(seed.encode('utf-8'))+1))+'END🙂\r\n'
        folder=RUN/'mixed-1MiB';nonce=configure(folder)
        new.generate_text(ARGS,folder,mixed);stress=receive(folder,mixed,nonce)
        negative=[]
        for mode in ('nonzero','timeout','overflow'):
            folder=RUN/'negative'/mode;configure(folder,mode)
            args=SimpleNamespace(**vars(ARGS));args.api_timeout=0.5 if mode=='timeout' else 10
            try:new.generate_text(args,folder,mixed)
            except lab.LabError as exc:
                assert exc.status=='API_ERROR'
                negative.append(dict(mode=mode,status=exc.status,stage=exc.stage))
            else:raise AssertionError('Negative mode did not fail: '+mode)
            result=batch.read(folder/'codex.json')
            if mode=='timeout':assert result['timeout'] and result['killed']
            if mode=='overflow':assert result['output_limit'] and result['killed']
            if mode=='nonzero':assert result['returncode']==7
        # A true transport failure is recorded and cannot be resent by the runner.
        job=dict(id='nonzero-no-resend');folder=RUN/'no-resend/jobs'/job['id']/'call';configure(folder,'nonzero')
        generation_plan=dict(model='OFFLINE_FIXTURE',reasoning='low',api_timeout=10,max_calls=1)
        failed=runner.generate(RUN/'no-resend',job,generation_plan,mixed)
        assert failed['status']=='API_ERROR'
        with patch.object(new,'generate_text',side_effect=AssertionError('must not resend')):
            assert runner.generate(RUN/'no-resend',job,generation_plan,mixed)==failed
    assert sum(r['status']=='CREATEPROCESS_ERROR' for r in baseline)==12
    assert sum(r['status']=='RECEIVED' for r in baseline)==4
    assert all(r['command_utf16_units']<32767 for r in newrows+[stress])
    assert historical()==before and runner.hashes()==sources
    summary=dict(status='PASS',real_model_calls=0,real_cli_generation_calls=0,
                 original_argv=dict(received=4,createprocess_winerror_206=12),
                 new_stdin=dict(branch_prompts=16,all_byte_exact=True,records=newrows,mixed_stress=stress),
                 negative=negative,failed_generation_no_resend=True,
                 preserved_bindings=len(before),source_files=len(sources),
                 default_proxy_regression='Original failures and loopback-isolated conditional pass retained byte-for-byte; not rerun',
                 label='OFFLINE_CLI_RECEIVER_ONLY; no real model/context acceptance claim')
    batch.atomic(RUN/'summary.json',summary)
    batch.atomic(RUN/'evidence-lock.json',{str(p.relative_to(RUN)):lab.digest(p.read_bytes()) for p in RUN.rglob('*') if p.is_file()})
    print(json.dumps({k:v for k,v in summary.items() if k!='new_stdin'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
