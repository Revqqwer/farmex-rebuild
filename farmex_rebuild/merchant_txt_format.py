"""Normal byte-format projection for004b99f8, not an executing file exporter.

Unicode-to-ANSI outputs are explicit inputs. No UTF8/default-CP guess, native
ostream receipt, file open/write/close, or actual bot export is synthesized.
"""
from dataclasses import dataclass
from merchant_result_filter import raw


def build_txt_header(view_text,category_text,search_text):
    if any(type(v) is not str for v in (view_text,category_text,search_text)):
        raise ValueError('Three explicit Unicode control texts required')
    return view_text+' - '+category_text+' - Filtre : '+search_text+' \n'


def build_txt_path(base_ansi,identity_helper_ansi,time_helper_ansi):
    if any(type(v) is not bytes for v in (base_ansi,identity_helper_ansi,time_helper_ansi)):
        raise ValueError('Explicit ANSI base and both helper outputs required')
    return base_ansi+b'\\'+identity_helper_ansi+b' Merchant Tarama '+time_helper_ansi+b'.txt'


@dataclass(frozen=True)
class MerchantTxtAnsiRow:
    index_dword:int
    seller_ansi:object=None
    item_ansi:object=None
    amount_ansi:object=None
    price_ansi:object=None
    def __post_init__(self):
        raw(self.index_dword,32,'source row index')
        for v in (self.seller_ansi,self.item_ansi,self.amount_ansi,self.price_ansi):
            if v is not None and type(v) is not bytes:raise ValueError('Explicit immutable ANSI conversion outputs required')


@dataclass(frozen=True)
class MerchantTxtProjection:
    complete:bool
    status:str
    insertion_chunks:tuple=()
    projected_CRT_text_bytes:bytes=b''
    needed:object=None
    read_order:tuple=()
    source_ostream_executed:bool=False
    file_written:bool=False
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


def project_txt_bytes(header_ansi,rows):
    """Project normal byte concatenation of uniformly converted ANSI fragments.

    Each source ostream C-string insertion stops at its first NUL independently.
    The CRT byte projection applies observed mode2 LF translation. Source stream
    width/fill/locale facets, failures and mixed-codepage string conversions are
    outside this scalar scope. Rows must be a frozen current displayed snapshot.
    """
    if header_ansi is not None and type(header_ansi) is not bytes:raise ValueError('Explicit ANSI header conversion required')
    if type(rows) is not tuple or any(not isinstance(r,MerchantTxtAnsiRow) for r in rows):
        raise ValueError('Immutable typed displayed-row observations required')
    chunks=[];reads=[]
    def result(ok,status,needed=None):
        return MerchantTxtProjection(ok,status,tuple(chunks),b''.join(chunks).replace(b'\n',b'\r\n'),needed,tuple(reads))
    if header_ansi is None:return result(False,'needs_ansi_header','header_ansi')
    chunks.append(header_ansi.split(b'\0',1)[0])
    for position,row in enumerate(rows):
        # Evaluation order is opposite the final displayed label order.
        for field in ('price_ansi','amount_ansi','item_ansi','seller_ansi'):
            reads.append((position,field))
            if getattr(row,field) is None:return result(False,'needs_ansi_row',(position,field))
        number=(row.index_dword+1)&0xffffffff
        if number>=0x80000000:number-=0x100000000
        line=(str(number).encode('ascii')+b' - Sat\xfdc\xfd : '+row.seller_ansi+
              b' Item : '+row.item_ansi+b' Adet : '+row.amount_ansi+b' Fiyat : '+row.price_ansi+b' \n')
        chunks.append(line.split(b'\0',1)[0])
    return result(True,'own_normal_format_projected')
