"""Richard004c8fdc/004c9078 local11-byte repair buffers. No transport."""


def repair_payload(kind,npc_id,slot_word,producer_item_id):
    if type(kind) is not int or kind not in (1,2):raise ValueError('Source repair kind1/2 required')
    for value in (npc_id,producer_item_id):
        if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Raw DWORD ID required')
    if type(slot_word) is not int or not 0<=slot_word<=0xffff:raise ValueError('Producer WORD slot required')
    slot=(slot_word if kind==1 else slot_word-14)&255
    return bytes((0x3b,kind,slot))+npc_id.to_bytes(4,'little')+producer_item_id.to_bytes(4,'little')
