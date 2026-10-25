"""Owned result-table state; not a source VCL object or game scan session.

Immutable decoded display records enter here after metadata projection. Search
conversion remains an explicit observation provider: Python upper/casefold is
never substituted for the source Unicode/ANSI conversion chain.
"""
from dataclasses import dataclass,replace
from merchant_result_filter import MerchantFilterSelection
from merchant_result_rows import MerchantDisplayRecord, build_merchant_result_rows
from merchant_windows_sort import sort_prepared_merchant_rows
from merchant_text_normalization import WindowsMerchantText

PREFIX = 'frmMain/MainTab/sheetMerchantScan/GroupBox47/'
KIND_PATH = PREFIX + 'cmbMerchantScanGoster'
CATEGORY_PATH = PREFIX + 'cmbScanMerchantItemTur'
SEARCH_PATH = PREFIX + 'txtMerchantScanSearchItemName'
TABLE_PATH = PREFIX + 'LwMerchantScan'
FILTER_PATHS = (KIND_PATH, CATEGORY_PATH, SEARCH_PATH)


@dataclass(frozen=True)
class MerchantTableUpdate:
    complete: bool
    status: str
    prepared: object
    sorting: object = None
    rows: tuple = ()
    live_compatibility_verified: bool = False
    text_observations: tuple = ()


class OwnedMerchantResults:
    def __init__(self):
        self.records = ()
        self.last = None

    def replace_records(self, records):
        if type(records) is not tuple or any(not isinstance(r, MerchantDisplayRecord) for r in records):
            raise ValueError('Immutable decoded display records required')
        self.records = records
        self.last = None

    def rebuild(self, kind, category, query, *, search_color=0, normalized_search=None,text_policy=None):
        if type(query) is not str:
            raise ValueError('Own current Unicode query required')
        length = len(query.encode('utf-16-le', errors='surrogatepass')) // 2
        selection = MerchantFilterSelection(kind, category, search_color, length, normalized_search)
        if text_policy is not None and not isinstance(text_policy,WindowsMerchantText):
            raise ValueError('Explicit own Windows text policy required')
        observations=[]
        prepared = build_merchant_result_rows(self.records, selection)
        def missing(status):
            self.last=MerchantTableUpdate(False,status,prepared,rows=prepared.rows,text_observations=tuple(observations))
            return self.last
        try:
            # Probe the pure filter first: a direction/category miss must not
            # fabricate an active query conversion or require byte metadata.
            if text_policy is not None and prepared.status=='needs_normalized_search':
                result=text_policy.query(query);observations.append(('query',None,result))
                if not result.complete:return missing('query_normalization:'+result.status)
                selection=replace(selection,normalized_search=result.output_bytes)
                prepared=build_merchant_result_rows(self.records,selection)
            if text_policy is not None and prepared.status=='needs_normalized_name':
                records=list(self.records)
                for index,record in enumerate(records):
                    f=record.filter_record
                    if f.direction_0c!=selection.direction or (selection.category!=-1 and f.category_1c!=selection.category):continue
                    if f.normalized_name is not None:continue
                    if f.original_name_ansi is None:break
                    result=text_policy.ansi_name(f.original_name_ansi);observations.append(('name',index,result))
                    if not result.complete:return missing('name_normalization:'+result.status)
                    records[index]=replace(record,filter_record=replace(f,normalized_name=result.output_bytes))
                prepared=build_merchant_result_rows(tuple(records),selection)
        except (OSError,ValueError) as error:
            return missing('local_text_conversion:'+str(error))
        if not prepared.formatting_complete:
            self.last = MerchantTableUpdate(False, prepared.status, prepared, rows=prepared.rows,text_observations=tuple(observations))
        else:
            sorting = sort_prepared_merchant_rows(prepared)
            self.last = MerchantTableUpdate(sorting.complete, sorting.status, prepared, sorting,
                sorting.rows if sorting.complete else (),text_observations=tuple(observations))
        return self.last

    def sort_column(self, column):
        if self.last is None or self.last.prepared is None or not self.last.prepared.formatting_complete:
            raise ValueError('Complete current row preparation required')
        # Re-sort the current displayed order, including duplicate rows. This
        # matters for non-total DWORD subtraction and equal-key permutations.
        prepared = replace(self.last.prepared, rows=self.last.rows)
        if not self.last.complete:
            raise ValueError('Complete current displayed order required')
        sorting = sort_prepared_merchant_rows(prepared, column)
        self.last = MerchantTableUpdate(sorting.complete, sorting.status, prepared, sorting,
            sorting.rows if sorting.complete else (),text_observations=self.last.text_observations)
        return self.last
