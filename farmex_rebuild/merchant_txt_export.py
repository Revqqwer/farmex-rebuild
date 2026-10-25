"""Executing owned TXT writer with explicit context and local codec policy.

No game context is discovered here. Source C++ stream/SEH equivalence is not
claimed; completed bytes are actual own file writes with explicit close result.
"""
from dataclasses import dataclass
from pathlib import Path
from merchant_export_context import build_source_time_fragment
from merchant_txt_format import build_txt_header,build_txt_path,MerchantTxtAnsiRow,project_txt_bytes
from merchant_result_rows import MerchantResultRow
from name_codec import WindowsNameCodec

BUTTON_PATH='frmMain/MainTab/sheetMerchantScan/GroupBox58/btnSaveMScanResults'


@dataclass(frozen=True)
class OwnedExportContext:
    directory:str
    identity_ansi:bytes
    tm_dwords:tuple
    text_code_page:int
    filesystem_code_page:int
    def __post_init__(self):
        if type(self.directory) is not str or not Path(self.directory).is_absolute():raise ValueError('Explicit absolute own output directory required')
        if type(self.identity_ansi) is not bytes:raise ValueError('Explicit final ANSI identity required')
        build_source_time_fragment(self.tm_dwords)
        for cp in (self.text_code_page,self.filesystem_code_page):
            if type(cp) is not int or not 1<=cp<=65535:raise ValueError('Two explicit nonzero codepages required')


@dataclass(frozen=True)
class OwnedTxtExportResult:
    complete:bool
    status:str
    path:object=None
    path_ansi:object=None
    rows_written:int=0
    bytes_written:int=0
    encoding_observations:tuple=()
    failed_row:object=None
    error:object=None
    close_error:object=None
    file_opened:bool=False
    file_closed:bool=False
    source_ostream_executed:bool=False
    source_default_codepage_verified:bool=False
    actual_game_context_verified:bool=False
    live_compatibility_verified:bool=False


def export_displayed_txt(context,view_text,category_text,search_text,rows,*,codec_factory=WindowsNameCodec,opener=open):
    """Write current displayed row order. A later error retains written prefix.

    Binary own IO receives pretranslated CRT text bytes. The owned writer keeps
    output inside the explicitly configured directory and does not mkdir.
    """
    if context is None:return OwnedTxtExportResult(False,'needs_export_context')
    if not isinstance(context,OwnedExportContext):raise ValueError('Typed own export context required')
    if type(rows) is not tuple or any(not isinstance(r,MerchantResultRow) for r in rows):raise ValueError('Immutable displayed row snapshot required')
    path=None;path_ansi=None;stream=None;closed=False;row_number=None
    count=0;written=0;observations=[];error=None;close_error=None;stage='header_conversion'
    def encode(codec,text,label):
        data,used=codec.encode(text)
        if type(data) is not bytes:raise ValueError('Codec must produce immutable bytes')
        observations.append((label,codec.code_page,data,used));return data
    def write(data):
        nonlocal written
        n=stream.write(data)
        if type(n) is not int or not 0<=n<=len(data):raise OSError('Invalid own write result')
        written+=n
        if n!=len(data):raise OSError('Short own file write')
    try:
        text_codec=codec_factory(context.text_code_page)
        header=encode(text_codec,build_txt_header(view_text,category_text,search_text),'header')
        stage='path_conversion';file_codec=codec_factory(context.filesystem_code_page)
        base=encode(file_codec,context.directory,'directory')
        path_ansi=build_txt_path(base,context.identity_ansi,build_source_time_fragment(context.tm_dwords))
        decoded=file_codec.decode(path_ansi.split(b'\0',1)[0])
        path=Path(decoded)
        root=Path(context.directory).resolve()
        # Explicit own namespace constraint; not a claimed source sanitization.
        path=path.resolve()
        path.relative_to(root)
        if path==root:raise ValueError('Export filename is the directory')
        stage='open';stream=opener(path,'wb')
        stage='header_write';write(project_txt_bytes(header,()).projected_CRT_text_bytes)
        for row_number,row in enumerate(rows):
            stage='row_conversion'
            if type(row.caption) is not str or len(row.subitems)<3:raise ValueError('Displayed caption/item/amount/price required')
            values={}
            for field,text in (('price_ansi',row.subitems[2]),('amount_ansi',row.subitems[1]),
                               ('item_ansi',row.subitems[0]),('seller_ansi',row.caption)):
                values[field]=encode(text_codec,text,(row_number,field))
            formatted=project_txt_bytes(b'',(MerchantTxtAnsiRow(row_number&0xffffffff,**values),))
            stage='row_write';write(formatted.projected_CRT_text_bytes)
            count+=1
        stage='close'
    except (OSError,ValueError) as e:error=str(e)
    finally:
        if stream is not None:
            try:stream.close();closed=True
            except OSError as e:close_error=str(e)
    ok=error is None and close_error is None
    return OwnedTxtExportResult(ok,'written' if ok else 'failed:'+stage,
        None if path is None else str(path),path_ansi,count,written,tuple(observations),
        row_number if stage.startswith('row_') and not ok else None,error,close_error,
        stream is not None,closed)
