"""Owned scan lifecycle; no native receipts, lookup provider or game polling.

Uses the source ordering with actual owned effects. This is separate from the
observation-only scan control planner and its native helper completion claims.
"""
from dataclasses import dataclass,replace
from merchant_scan_control import MerchantScanOptions,ScanControlState,signed32
from rtl_integer32 import parse_rtl_integer32

PREFIX='frmMain/MainTab/sheetMerchantScan/'
BUY_PATH=PREFIX+'GroupBox58/chScanBuyMerchant'
SELL_PATH=PREFIX+'GroupBox58/chScanSellMerchant'
SAVE_PATH=PREFIX+'GroupBox58/chMerchantScanAfterSaveTXT'
ROUTE_PATH=PREFIX+'GroupBox15/chMerchantScanWithRoute'
ROUTE_LIST=PREFIX+'GroupBox15/PazarTaraKordList'
START_PATH=PREFIX+'GroupBox58/btnPazarDolasStart'
STOP_PATH=PREFIX+'GroupBox58/btnPazarDolasStop'
QUICK_PATH=PREFIX+'GroupBox58/btnTara'
STATUS_PATH=PREFIX+'GroupBox58/lblpazardolasdurum'
SETTING_PATHS=(SELL_PATH,BUY_PATH,SAVE_PATH,ROUTE_PATH)


@dataclass(frozen=True)
class OwnedScanUpdate:
    complete:bool
    status:str
    state:ScanControlState
    failed_row:object=None
    failed_coordinate:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class OwnedMerchantScan:
    def __init__(self):
        self.state=ScanControlState()
        self.last=None

    def configure(self,index,sell,buy,save,route):
        if type(index) is not int or not -0x80000000<=index<=0xffffffff:
            raise ValueError('Own combo index required')
        if any(type(v) is not bool for v in (sell,buy,save,route)):
            raise ValueError('Own checkbox booleans required')
        self.state=replace(self.state,options=MerchantScanOptions(
            int(signed32(index&0xffffffff)>0),int(sell),int(buy),int(save),int(route)))
        return self.state.options

    def start(self,sell,buy,rows,clear_results,set_button,set_mode,set_status):
        """Rows is a reader returning own immutable (X text,Y text) pairs.

        UI effects run at their reached positions. They do not certify source
        native helpers; exceptions propagate with prior own changes preserved.
        """
        if type(sell) is not bool or type(buy) is not bool:raise ValueError('Own live checkbox values required')
        def done(ok,status,row=None,coord=None):
            self.last=OwnedScanUpdate(ok,status,self.state,row,coord);return self.last
        for field in ('vector_78','vector_58','route_points'):
            self.state=replace(self.state,**{field:()})
        self.state=replace(self.state,route_index_dword=0,result_records=())
        clear_results()
        self._buttons((0,1,0),set_button)
        if not sell and buy:
            set_mode(1)
            self.state=replace(self.state,options=replace(self.state.options,view_mode_dword=1))
        if self.state.options.route_byte:
            for index,pair in enumerate(rows()):
                if type(pair) is not tuple or len(pair)!=2 or any(type(s) is not str for s in pair):
                    raise ValueError('Own immutable X/Y Unicode pairs required')
                values=[]
                for label,text in zip(('x','y'),pair):
                    value=parse_rtl_integer32(text)
                    if not value.accepted:return done(False,'route_integer_rejected',index,label)
                    values.append(value.dword)
                self.state=replace(self.state,route_points=self.state.route_points+(tuple(values),))
        self.state=replace(self.state,active_byte=1)
        set_status('Taraniyor...')
        self.state=replace(self.state,status_text='Taraniyor...')
        return done(True,'waiting_for_runtime_data')

    def _buttons(self,states,set_button):
        for index,enabled in enumerate(states):
            set_button(index,bool(enabled))
            values=list(self.state.button_enabled);values[index]=enabled
            self.state=replace(self.state,button_enabled=tuple(values))

    def stop(self,set_button,set_status,completed=False):
        if type(completed) is not bool:raise ValueError('Own completion boolean required')
        self.state=replace(self.state,active_byte=0,busy_byte_0f=0)
        self._buttons((1,0,1),set_button)
        text='Tarama Tamamlandi !' if completed else 'Hazır'
        set_status(text);self.state=replace(self.state,status_text=text)
        self.last=OwnedScanUpdate(True,'stopped',self.state)
        return self.last

    def interrupt_for_movement(self,set_button):
        """Cell GIT clears flags/buttons before coordinate parsing, no label set."""
        self.state=replace(self.state,active_byte=0,busy_byte_0f=0)
        self._buttons((1,0,1),set_button)
        self.last=OwnedScanUpdate(True,'interrupted_by_movement',self.state)
        return self.last
