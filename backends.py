"""Simulation adapters. Generation and scheduling do not depend on tool syntax."""
from typing import Protocol
from pathlib import Path
import uuid


class SimulationBackend(Protocol):
    name: str

    def evaluate(self, folder: Path, spec: dict, tools: dict, args, secret: str) -> dict: ...


class IcarusBackend:
    name = 'icarus'

    def evaluate(self, folder, spec, tools, args, secret=''):
        import rtl_lab as lab
        row = {'backend': self.name}
        result = lab.run_process([tools['iverilog']['path'], '-g2012', '-Wall', '-s', 'tb',
                                  '-o', 'simulation.vvp', 'dut.sv', 'testbench.sv'], folder, args.compile_timeout)
        lab.save_process(folder, 'compile', result, secret)
        row['compile_seconds'] = result['elapsed_seconds']
        if result['timeout']:
            return dict(row, status='TIMEOUT', stage='compile', message='Compiler wall timeout')
        if result['output_limit'] or result['returncode'] != 0:
            return dict(row, status='COMPILE_FAIL', stage='compile', message='See compile.stderr.log')
        nonce = uuid.uuid4().hex
        result = lab.run_process([tools['vvp']['path'], '-N', 'simulation.vvp', '+nonce=' + nonce], folder, args.sim_timeout)
        lab.save_process(folder, 'simulate', result, secret)
        receipt = folder / 'verdict.txt'
        text = receipt.read_text(encoding='utf-8', errors='replace') if receipt.is_file() else ''
        status, message = lab.judge_simulation(result, text, spec['checks'], nonce)
        return dict(row, status=status, message=message, stage='simulate', receipt_nonce=nonce,
                    simulate_seconds=result['elapsed_seconds'])


BACKENDS = {'icarus': IcarusBackend}
