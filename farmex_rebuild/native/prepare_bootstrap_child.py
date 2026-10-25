"""Generate a parent pin from the just-compiled own child; does not execute it."""
import hashlib,struct,sys
from pathlib import Path
path=Path(sys.argv[1]);destination=Path(sys.argv[2]);data=path.read_bytes()
pe=struct.unpack_from('<I',data,60)[0];opt=pe+24
assert data[:2]==b'MZ' and data[pe:pe+4]==b'PE\0\0'
assert struct.unpack_from('<H',data,pe+4)[0]==0x14c and struct.unpack_from('<H',data,opt)[0]==0x10b
base=struct.unpack_from('<I',data,opt+28)[0];assert base==0x400000
assert not struct.unpack_from('<H',data,opt+70)[0]&0x40
table=opt+struct.unpack_from('<H',data,pe+20)[0]
sections=[struct.unpack_from('<4I',data,table+i*40+8) for i in range(struct.unpack_from('<H',data,pe+6)[0])]
def raw(rva,n):
    section=next(s for s in sections if s[1]<=rva and rva+n<=s[1]+s[2]);offset=section[3]+rva-section[1]
    result=data[offset:offset+n];assert len(result)==n;return result
def string(rva):
    chars=[]
    for i in range(128):
        char=raw(rva+i,1)
        if char==b'\0':return b''.join(chars).decode('ascii')
        chars.append(char)
    raise ValueError('Unterminated own export name')
rva,size=struct.unpack_from('<II',data,opt+96);export=struct.unpack('<IIHHIIIIIII',raw(rva,40))
function_count,name_count,functions,names,ordinals=export[6:]
matches=[];source_helpers={}
for i in range(name_count):
    name=string(struct.unpack('<I',raw(names+4*i,4))[0])
    canonical=name.lstrip('_').split('@')[0]
    if canonical in ('FarmexSourcePreflight','FarmexSourcePublish'):
        ordinal=struct.unpack('<H',raw(ordinals+2*i,2))[0];assert ordinal<function_count
        target=struct.unpack('<I',raw(functions+4*ordinal,4))[0];assert not rva<=target<rva+size
        assert canonical not in source_helpers;source_helpers[canonical]=target
    if name in ('FarmexFixtureBootstrap','FarmexFixtureBootstrap@4','_FarmexFixtureBootstrap@4'):
        ordinal=struct.unpack('<H',raw(ordinals+2*i,2))[0];assert ordinal<function_count
        target=struct.unpack('<I',raw(functions+4*ordinal,4))[0];assert not rva<=target<rva+size
        matches.append(target)
assert len(matches)==1
extra=''
if len(sys.argv)==4:
    assert sys.argv[3]=='--source-worker'
    assert set(source_helpers)=={'FarmexSourcePreflight','FarmexSourcePublish'}
    extra='#define OWN_SOURCE_PREFLIGHT_RVA 0x%x\n#define OWN_SOURCE_PUBLISH_RVA 0x%x\n'%(source_helpers['FarmexSourcePreflight'],source_helpers['FarmexSourcePublish'])
else:assert len(sys.argv)==3
digest=hashlib.sha256(data).digest()
destination.write_text('#define OWN_CHILD_SIZE %d\n#define OWN_CHILD_BASE 0x%x\n#define OWN_BOOTSTRAP_RVA 0x%x\n'%(len(data),base,matches[0])+
 extra+'static const BYTE own_child_sha256[32]={'+','.join('0x%02x'%b for b in digest)+'};\n',encoding='ascii')
print('Own child pinned: '+digest.hex())
