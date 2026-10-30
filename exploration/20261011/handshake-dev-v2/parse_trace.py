def parse_trace(p):
 def number(x,base):return x if any(c in x.lower() for c in 'xz') else int(x,base)
 rows=[]
 for line in p.read_text().splitlines():
  t=line.split()
  if len(t)!=14:raise ValueError('Bad trace row width')
  endpoints=[]
  for i in (2,6,10):endpoints.append(dict(valid=number(t[i],2),ready=number(t[i+1],2),data=number(t[i+2],16),last=number(t[i+3],2)))
  rows.append(dict(cycle=int(t[0]),rst=number(t[1],2),s=endpoints[0],m=endpoints[1:]))
 return rows
