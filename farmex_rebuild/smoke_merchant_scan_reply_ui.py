"""Actual timer -> request queue -> supplied reply -> table/finish queue."""
import copy
import struct
import time
from action_queue import enqueue
from direct_chat_packets import QueueAttempt
from merchant_scan import ScanSnapshot
from merchant_scan_collection import MerchantProbe
from merchant_scan_pipeline import ScanConsumeObservation
from merchant_scan_loop import ScanLoopInput
from merchant_scan_reply_frame import ScanReplyObservation
from merchant_scan_results import MerchantActorMetadata,MerchantItemMetadata
from merchant_scan_runtime import START_PATH,STOP_PATH,ROUTE_PATH,SELL_PATH,BUY_PATH
from merchant_results_session import KIND_PATH,CATEGORY_PATH,SEARCH_PATH,TABLE_PATH
from merchant_scan_reply_source import ScanReplySource
from merchant_actor_metadata import MerchantActorObservation,MerchantCoordinateObservation
from merchant_item_metadata import MerchantItemObservation
from item_lookup import BaseItemLookupObservation,ExtensionLookupObservation
from item_name import ItemNameObservation


def check_merchant_scan_reply_ui(app):
    p=app.panel;root=p.canvas.winfo_toplevel()
    saved=dict(p.values);lists=copy.deepcopy(p.lists);form=p.form.get()
    saved_queue=p.flood_session.queue;clock=p.flood_clock
    phase={'enqueue_return':False,'finish_return':False,'source':False,'code_page':None}
    empty={i:MerchantProbe(0) for i in range(5001)}
    probes=dict(empty);probes[0]=MerchantProbe(123,1,3,4,0,9.5,42)
    normals=dict.fromkeys(('head_capture','target_write','packet_copy','erase_iterator',
        'erase_move','erase_tail','iterator_cleanup'),True)
    payload=b'\x68\x23\x01\x2a\x00'+struct.pack('<IHHI',123456,2,99,1000)+b'\0'*(11*12)
    def pump_until(predicate):
        deadline=time.monotonic()+4
        while not predicate():
            if time.monotonic()>deadline:raise AssertionError('Reply timer did not reach expected state')
            root.update();time.sleep(.005)
    def provider(context):
        if context.reply is not None:
            assert context.reply.payload==payload
            if phase['source']:
                def pad(data):return data+b'\0'+b'x'*(254-len(data))
                actor=MerchantActorObservation(True,0x1000,
                    MerchantCoordinateObservation(0x10,True,True,825),
                    MerchantCoordinateObservation(0x14,True,True,0xffffffff),
                    0x18,4,0x20,0,0x30,True,pad(b'KaynakSat\xfdc\xfd'))
                item=MerchantItemObservation(
                    BaseItemLookupObservation(first_variant_byte=1,function_target=0x9000,call_returned=True,result_eax=0x2000),
                    2,ExtensionLookupObservation(0x4000,0x5000,0x9004,True,0x3000),
                    11,107,ItemNameObservation(metadata_category=2,storage_dword=4,pointer_dword=0,
                        bad_read_result=0,captured=pad(b'Yay\xfd')),12)
                return ScanLoopInput(reply=ScanReplyObservation(parse_returned=True,finish_setup_returned=True,
                    finish_returned=True,attempt=QueueAttempt(1,1020,True),
                    source=ScanReplySource(actor,{0:item},phase['code_page'])))
            return ScanLoopInput(reply=ScanReplyObservation(
                MerchantActorMetadata('reply seller',825,0xffffffff),
                {0:MerchantItemMetadata('Bow',5,5,7,base_name_ansi=b'Bow')},
                True,True,phase['finish_return'],QueueAttempt(1,1010,phase['enqueue_return'])))
        return ScanLoopInput(ScanSnapshot(collect_returned=True,consume_returned=True),probes,
            ScanConsumeObservation(True,True,2,normal_returns=normals,attempt=QueueAttempt(1,1000,True)))
    try:
        p.form.set('frmMain');p.render();p.section.set('Merchant Tarama');p.select_sections()
        p.values[ROUTE_PATH]=False;p.values[SELL_PATH]=True;p.values[BUY_PATH]=True
        p.values[KIND_PATH]=1;p.values[CATEGORY_PATH]=0;p.values[SEARCH_PATH]=''
        p.configure_merchant_scan();p.flood_clock=lambda:1000
        p.merchant_scan_provider=provider
        p.widgets[START_PATH].invoke()
        pump_until(lambda:bool(p.merchant_scan.state.busy_byte_0f))
        request_count=len(p.flood_session.queue.records)
        assert request_count==len(saved_queue.records)+1
        assert p.flood_session.queue.records[-1].payload==bytes.fromhex('68112a00')
        ticket=p.receive_merchant_scan_reply(payload)
        assert ticket is not None
        pump_until(lambda:p.merchant_scan_loop_result.reply is not None)
        update=p.merchant_scan_loop_result
        assert update.reply.status=='needs_finish_enqueue'
        assert p.merchant_scan.state.busy_byte_0f==1
        assert len(p.merchant_results.records)==1
        assert p.merchant_result_update.complete
        table=p.widgets[TABLE_PATH]
        assert len(table.get_children())==1
        row=tuple(table.item(table.get_children()[0],'values'))
        assert row[:4]==('reply seller','Bow(+7)','2','1.000'),row
        assert p.flood_session.queue.records[-1].payload==b'\x68\x27'
        p.flood_session.queue=enqueue(p.flood_session.queue,b'other feature',13,0,1,1011).state
        count=len(p.flood_session.queue.records)
        phase['enqueue_return']=True
        pump_until(lambda:p.merchant_scan_loop_result.reply is not None and
            p.merchant_scan_loop_result.reply.status=='needs_finish_return')
        assert p.merchant_scan.state.busy_byte_0f==1
        assert len(p.flood_session.queue.records)==count
        assert p.flood_session.queue.records[-1].payload==b'other feature'
        phase['finish_return']=True
        pump_until(lambda:p.merchant_scan.state.busy_byte_0f==0)
        assert len(p.merchant_results.records)==1
        assert len(p.merchant_scan.state.result_records)==1
        assert len(p.flood_session.queue.records)==count
        # The same actual timer/table path now accepts raw lookup/read/copy
        # observations. Missing codepage holds the result; no ready-made Unicode
        # seller/item text is supplied in this phase.
        phase['source']=True
        assert p.receive_merchant_scan_reply(payload) is not None
        pump_until(lambda:p.merchant_scan_loop_result.reply is not None and
            p.merchant_scan_loop_result.reply.source_production is not None)
        assert len(p.merchant_results.records)==1
        assert len(p.flood_session.queue.records)==count
        phase['code_page']=1254
        pump_until(lambda:len(p.merchant_results.records)==2)
        record=p.merchant_results.records[1]
        assert (record.seller,record.item_name)==('KaynakSatıcı','Yayı(+7) (Reverse)')
        assert record.filter_record.category_1c==12
        assert record.filter_record.original_name_ansi==b'Yay\xfd(+7) (Reverse)'
        assert len(p.merchant_scan.state.result_records)==2
        rows={tuple(table.item(i,'values')) for i in table.get_children()}
        assert any(r[:2]==('KaynakSatıcı','Yayı(+7) (Reverse)') for r in rows)
        assert len(p.flood_session.queue.records)==count+1
        p.widgets[STOP_PATH].invoke()
        assert p.receive_merchant_scan_reply(payload) is None
        assert p.merchant_scan_after_id is None
        p.bind_document(dict(saved),copy.deepcopy(lists))
        assert p.merchant_scan_loop.context(p.merchant_scan.state,p.flood_session.queue).reply is None
        assert not p.merchant_results.records
        print('Merchant scan reply UI passed: actual timer collection/consume request, explicit reply FIFO, derived table row, partial finish queue, separate parent return, busy clear, interleaved writer and stop/profile invalidation; no game capture or send')
        print('Merchant reply source UI passed: raw actor/coordinate/lookup/name-copy observations, missing codepage hold, explicit1254 derived Turkish seller/item names, preserved ANSI and separate categories, one final queue entry')
    finally:
        p.flood_clock=clock;p.flood_session.queue=saved_queue
        app.values.clear();app.values.update(saved)
        app.lists.clear();app.lists.update(lists)
        p.form.set(form);p.bind_document(app.values,app.lists)
