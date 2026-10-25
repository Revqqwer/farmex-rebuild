"""Extract own bounded x86 worker, reject absolute PE fixups in its code."""
import hashlib,json,struct,sys
from pathlib import Path
path=Path(sys.argv[1]);directory=Path(sys.argv[2]);data=path.read_bytes()
pe=struct.unpack_from('<I',data,60)[0];opt=pe+24;base=struct.unpack_from('<I',data,opt+28)[0]
assert data[:2]==b'MZ' and data[pe:pe+4]==b'PE\0\0' and struct.unpack_from('<H',data,pe+4)[0]==0x14c
table=opt+struct.unpack_from('<H',data,pe+20)[0]
sections=[struct.unpack_from('<4I',data,table+40*i+8) for i in range(struct.unpack_from('<H',data,pe+6)[0])]
def raw(rva,n):
    s=next(s for s in sections if s[1]<=rva and rva+n<=s[1]+s[2]);at=s[3]+rva-s[1]
    result=data[at:at+n];assert len(result)==n;return result
def string(rva):
    result=[]
    for i in range(128):
        b=raw(rva+i,1)
        if b==b'\0':return b''.join(result).decode('ascii')
        result.append(b)
    raise ValueError('Unterminated own export')
rva,size=struct.unpack_from('<II',data,opt+96);exp=struct.unpack('<IIHHIIIIIII',raw(rva,40))
fc,nc,functions,names,ordinals=exp[6:];found={}
for i in range(nc):
    name=string(struct.unpack('<I',raw(names+4*i,4))[0]).split('@')[0].lstrip('_')
    if name in ('FarmexOwnWorker','FarmexOwnWorkerEnd'):
        ordinal=struct.unpack('<H',raw(ordinals+2*i,2))[0];assert ordinal<fc
        found[name]=struct.unpack('<I',raw(functions+ordinal*4,4))[0]
start,end=found['FarmexOwnWorker'],found['FarmexOwnWorkerEnd'];assert 0<end-start<=8192
code=raw(start,end-start)
rva,size=struct.unpack_from('<II',data,opt+96+5*8);offset=0;fixups=[]
while offset<size:
    page,length=struct.unpack('<II',raw(rva+offset,8));assert length>=8 and length<=size-offset
    for value in struct.unpack('<%dH'%((length-8)//2),raw(rva+offset+8,length-8)):
        if value and start<=page+(value&0xfff)<end:fixups.append(page+(value&0xfff))
    offset+=length
assert not fixups,'Worker has absolute relocations; do not copy or run'
(directory/'own_worker_bytes.h').write_text('static const BYTE own_worker_bytes[]={'+','.join('0x%02x'%b for b in code)+'};\n',encoding='ascii')
metadata=dict(template_sha256=hashlib.sha256(data).hexdigest(),worker_sha256=hashlib.sha256(code).hexdigest(),
 base=base,start_rva=start,end_rva=end,size=len(code),absolute_worker_fixups=fixups,
 direct_call_audit_pending=True)
(directory/'worker_metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
(directory/'worker_seed.tsv').write_text('0x%08x\town\tFarmexOwnWorker\n'%(base+start),encoding='ascii')
print(json.dumps(metadata))
