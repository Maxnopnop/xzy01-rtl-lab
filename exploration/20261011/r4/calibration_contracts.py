"""Handwritten correct contracts ONLY for mechanism calibration, never main model prompts."""
def contract(task):
    if task=='epoch_commit':
        reg={n:dict(width=2,reset=0) for n in ('l0','l1','s0','s1','mask')};reg['pulse']=dict(width=1,reset=0)
        w0='(data if write and slot == 0 else s0)';w1='(data if write and slot == 1 else s1)'
        mask='(mask | (2 if slot else 1) if write else mask)'
        nxt=dict(l0=f'{w0} if commit and ({mask} & 1) and not abort_tx else l0',l1=f'{w1} if commit and ({mask} & 2) and not abort_tx else l1',s0=f'l0 if abort_tx else {w0}',s1=f'l1 if abort_tx else {w1}',mask=f'0 if abort_tx or commit else {mask}',pulse='1 if commit and not abort_tx else 0')
        out=dict(visible='(l1 if read_slot else l0) if rst_n else 0',dirty='mask',committed='pulse')
    elif task=='refund_credit':
        reg=dict(balance=dict(width=3,reset=0),accept=dict(width=1,reset=0),reject=dict(width=1,reset=0))
        funded='(5 if balance + refund > 5 else balance + refund)';pay=f'(submit and cost != 0 and {funded} >= cost)'
        nxt=dict(balance=f'{funded} - cost if {pay} else {funded}',accept=f'1 if {pay} else 0',reject=f'1 if submit and not {pay} else 0')
        out=dict(credit='balance',accepted='accept',rejected='reject',can_pay=f'1 if rst_n and cost != 0 and {funded} >= cost else 0')
    else:
        reg={n:dict(width=1,reset=0) for n in ('va','vb','ta','tb','pulse')};reg.update({n:dict(width=2,reset=0) for n in ('da','db','res')})
        a='(atag if av else ta)';b='(btag if bv else tb)';hit=f'((av or va) and (bv or vb) and {a} == {b})'
        nxt=dict(va=f'0 if flush or {hit} else (1 if av else va)',vb=f'0 if flush or {hit} else (1 if bv else vb)',ta=f'0 if flush else {a}',tb=f'0 if flush else {b}',da='0 if flush else (adata if av else da)',db='0 if flush else (bdata if bv else db)',pulse=f'1 if not flush and {hit} else 0',res=f'0 if flush else ((adata if av else da) ^ (bdata if bv else db) if {hit} else res)')
        out=dict(pending_a='va',pending_b='vb',joined='pulse',result='res')
    return dict(timing=dict(edge='rising',reset='async_low'),registers=reg,next=nxt,outputs=out)
