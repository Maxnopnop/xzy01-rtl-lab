"""Generate RTL through the user's existing ChatGPT-authenticated Codex CLI."""
import json
import os
from pathlib import Path
import shutil

import rtl_lab as lab


def find_codex(override=None):
    if override:
        candidate = Path(override)
        if candidate.is_file() and candidate.suffix.lower() not in ('.cmd', '.ps1', '.bat'):
            return str(candidate.resolve())
        raise lab.LabError('ENV_ERROR', 'codex_config', '--codex-executable must be a native executable')
    candidate = shutil.which('codex.exe' if os.name == 'nt' else 'codex')
    if candidate:
        return candidate
    if os.name == 'nt':
        npm = Path(os.environ.get('APPDATA', '')) / 'npm/node_modules/@openai/codex/node_modules/@openai'
        matches = sorted(npm.glob('codex-win32-*/vendor/*/bin/codex.exe'))
        if matches:
            return str(matches[0])
    raise lab.LabError('ENV_ERROR', 'codex_config', 'Codex CLI executable not found')


def generate(args, folder, spec):
    exe = find_codex(args.codex_executable)
    env = lab.clean_env()
    for name in ('APPDATA', 'LOCALAPPDATA', 'CODEX_HOME'):
        if os.environ.get(name):
            env[name] = os.environ[name]
    # API-key environment variables are deliberately absent; Codex manages auth.
    for label, command in [('codex_version', [exe, '--version']),
                           ('codex_auth', [exe, 'login', 'status'])]:
        result = lab.run_process(command, folder, 15, env)
        lab.save_process(folder, label, result)
        if result['returncode'] != 0 or result['timeout']:
            raise lab.LabError('ENV_ERROR', 'codex_auth', 'Codex version/login check failed')
        if label == 'codex_auth' and 'Logged in using ChatGPT' not in result['stdout'] + result['stderr']:
            raise lab.LabError('ENV_ERROR', 'codex_auth', 'This mode requires existing ChatGPT login, not API-key auth')
    prompt = lab.SYSTEM_PROMPT + '\n\n' + spec['spec'] + '\n\nReply directly with the RTL. Do not invoke tools, read files, run tests, or delegate.\n'
    lab.write_text(folder / 'codex_prompt.txt', prompt)
    working = folder / 'generation_workspace'
    working.mkdir()
    output = folder / 'model_output.raw.txt'
    command = [exe, 'exec', '--ignore-user-config', '--ephemeral', '--skip-git-repo-check',
               '--sandbox', 'read-only', '--model', args.model, '--json', '--color', 'never',
               '-c', 'model_provider="openai"', '-c', 'forced_login_method="chatgpt"',
               '-c', f'model_reasoning_effort="{args.codex_reasoning}"',
               '-c', 'approval_policy="never"', '-c', 'project_doc_max_bytes=0',
               '-c', 'web_search="disabled"']
    for feature in ('shell_tool', 'multi_agent', 'apps', 'plugins', 'remote_plugin',
                    'hooks', 'memories', 'image_generation', 'computer_use', 'browser_use',
                    'in_app_browser', 'skill_search'):
        command.extend(['--disable', feature])
    command.extend(['--output-last-message', str(output), prompt])
    lab.write_json(folder / 'codex_request.json', {
        'transport': 'codex_exec_chatgpt_login', 'requested_model': args.model,
        'reasoning_effort': args.codex_reasoning, 'prompt': prompt,
        'temperature': None, 'seed': None, 'max_output_tokens': None,
        'sampling_note': 'CLI defaults; no temperature/seed/token limit sent',
        'codex_executable_sha256': lab.digest(Path(exe).read_bytes()),
        'cli_auth': 'ChatGPT (confirmed by login status)',
        'server_model_snapshot': 'Not exposed by exec JSONL; requested model is recorded without claiming a snapshot'})
    result = lab.run_process(command, working, args.api_timeout, env)
    lab.save_process(folder, 'codex', result)
    if result['timeout']:
        raise lab.LabError('API_ERROR', 'codex_timeout', 'Codex wall timeout; process tree cleaned up')
    if result['returncode'] != 0 or result['output_limit']:
        raise lab.LabError('API_ERROR', 'codex', 'Codex failed; inspect codex stderr/events')
    try:
        events = [json.loads(line) for line in result['stdout'].splitlines() if line.strip()]
    except ValueError:
        raise lab.LabError('API_ERROR', 'codex', 'Invalid Codex JSONL event stream') from None
    completed = [e for e in events if e.get('type') == 'turn.completed']
    if not completed or any(e.get('type') in ('error', 'turn.failed') for e in events):
        raise lab.LabError('API_ERROR', 'codex', 'No clean completed model turn')
    item_types = {e.get('item', {}).get('type') for e in events if e.get('type', '').startswith('item.')}
    if item_types - {'agent_message', 'reasoning'}:
        raise lab.LabError('RTL_REJECTED', 'codex_tools', 'Generation used tools; invalid for this direct-generation test')
    if not output.is_file():
        raise lab.LabError('API_ERROR', 'codex', 'Codex did not save a final answer')
    raw = output.read_text(encoding='utf-8')
    if not raw.strip():
        raise lab.LabError('API_ERROR', 'codex', 'Empty Codex answer')
    return raw, {'response_model': None, 'model_identity_basis': 'Explicit --model; exec does not expose backend snapshot',
                 'usage': completed[-1].get('usage'), 'generation_seconds': result['elapsed_seconds'],
                 'codex_generation_success': True, 'tools_used': False,
                 'codex_thread_id': next((e.get('thread_id') for e in events if e.get('type') == 'thread.started'), None)}
