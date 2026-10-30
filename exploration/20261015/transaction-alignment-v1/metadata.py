"""Development task metadata, separate from immutable R6 TASKS."""
INPUTS=[('s_valid',1),('s_data',8),('s_last',1),('m_ready0',1),('m_ready1',1)]
OUTPUTS=[('s_ready',1),('m_valid0',1),('m_data0',8),('m_last0',1),('m_valid1',1),('m_data1',8),('m_last1',1)]
TASKS={'development_broadcast':dict(inputs=INPUTS,outputs=OUTPUTS)}
def unpack(task,value):
 out={}
 for name,width in reversed(TASKS[task]['inputs']):out[name]=value&((1<<width)-1);value>>=width
 return out
def pack(values,ports):
 v=0
 for name,width in ports:v=(v<<width)|(values[name]&((1<<width)-1))
 return v
def unpack_outputs(value):
 out={}
 for name,width in reversed(OUTPUTS):out[name]=value&((1<<width)-1);value>>=width
 return out
def episodes(scene):
 if scene in (0,4):return [dict(beats=[[17+i,int(i==2)] for i in range(3)],termination='reset'),dict(beats=[[161+i,int(i==2)] for i in range(3)],termination='drain')]
 return [dict(beats=[[32+i,int(i==7)] for i in range(8)] if scene==1 else [[81,1]] if scene in (2,3) else [[17+i,int(i==2)] for i in range(3)],termination='drain')]
def ready(scene,cycle):
 if scene in (0,4):return (1,int(cycle>=10))
 if scene==3:return (int(cycle>=7),int(cycle>=7))
 return (1,1)
def is_reset(scene,cycle):return cycle<3 or (scene in (0,4) and cycle in (8,9))
