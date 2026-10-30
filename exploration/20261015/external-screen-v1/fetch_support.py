"""Continue original cumulative static access ledger, never repeat a URL."""
import json
import fetch_sources as f
R=f.R
base=json.loads((R/'access.json').read_text());original_count=len(base['requests'])
assert original_count==13 and not (R/'access-continuation.json').exists()
f.access=list(base['requests']);f.count=base['raw_files'];f.total=base['raw_bytes']
def flush():
 f.save(R/'access-continuation.json',dict(original_ledger='access.json',requests=f.access[original_count:],cumulative_requests=len(f.access),cumulative_raw_files=f.count,cumulative_raw_bytes=f.total,retries=0))
f.flush=flush
revisions=json.loads((R/'revisions.json').read_text())
wanted={
 'opentitan':['hw/ip/prim/doc/prim_packer.md','hw/ip/prim/fpv/tb/prim_packer_tb.sv','hw/ip/prim/dv/prim_alert/data/prim_alert_testplan.hjson','hw/ip/prim/dv/prim_alert/tb/prim_alert_tb.sv','hw/ip/prim/fpv/vip/prim_alert_rxtx_assert_fpv.sv','hw/ip/prim/dv/prim_esc/data/prim_esc_testplan.hjson','hw/ip/prim/dv/prim_esc/tb/prim_esc_tb.sv','hw/ip/prim/fpv/vip/prim_esc_rxtx_assert_fpv.sv','hw/top_earlgrey/ip_autogen/alert_handler/doc/theory_of_operation.md','hw/ip/prim/rtl/prim_diff_decode.sv','hw/ip/prim/rtl/prim_alert_pkg.sv','hw/ip/prim/rtl/prim_esc_pkg.sv'],
 'i2c':['doc/i2c_specs.pdf','bench/verilog/i2c_slave_model.v','bench/verilog/tst_bench_top.v','bench/verilog/wb_master_model.v']}
for short,names in wanted.items():
 rev=revisions[short];tree=json.loads((R/'metadata'/f'{short}-tree.json').read_text());paths={x['path'] for x in tree['tree'] if x['type']=='blob'}
 for name in names:
  assert name in paths,name
  f.get(f'https://raw.githubusercontent.com/{rev["repo"]}/{rev["commit"]}/{name}',R/'upstream'/short/name,512*1024,'raw')
flush();print(json.dumps(dict(cumulative_requests=len(f.access),raw_files=f.count,raw_bytes=f.total)))
