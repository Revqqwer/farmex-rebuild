"""Consumed-input replay frames for existing inventory/name operand models."""
from dataclasses import replace
from mining_slot_name import SlotNameObservation,plan_slot_name
from item_name import ItemNameObservation
from upgrade_packets import UpgradeItemObservation,plan_upgrade_item

ITEM_FIELDS={'global root slot':'global_root_slot','inventory offset':'inventory_offset',
 'records offset':'records_offset','base pointer':'base_pointer','variant pointer':'variant_pointer',
 'base item':'base_item','variant item':'variant_item'}
NAME_FIELDS={'IsBadReadPtr:EAX':'bad_read_result','complete_captured_bytes':'captured'}

class InventoryGetterFrame:
    def __init__(self,slot,*,name=False):
        self.slot=slot;self.name=name
        self.observation=SlotNameObservation() if name else UpgradeItemObservation()
        self.final=None

    def advance(self,o):
        expected=SlotNameObservation if self.name else UpgradeItemObservation
        if not isinstance(o,expected):raise ValueError('Typed inventory getter observation required')
        if self.final is not None:return self.final
        for _ in range(32):
            p=plan_slot_name(self.slot,self.observation) if self.name else plan_upgrade_item(self.slot,self.observation)
            complete=p.ansi_bytes is not None if self.name else p.complete
            if complete:self.final=p;return p
            missing=p.missing
            nested=self.name and p.name_plan is not None
            if nested:
                if p.name_plan.status!='needs_observation':return p #Unresolved source path, no invented fallback.
                field=NAME_FIELDS.get(missing.split(':')[0],missing)
                if missing.startswith('IsBadReadPtr:'):field='bad_read_result'
                source=o.name or ItemNameObservation();cached=self.observation.name or ItemNameObservation()
            else:
                field=missing if self.name else ITEM_FIELDS.get(missing,missing)
                source=o;cached=self.observation
            if not hasattr(source,field):raise ValueError('Unknown inventory getter operand gap: '+missing)
            value=getattr(source,field)
            if value is None:return p
            previous=getattr(cached,field)
            if field=='captured' and previous is not None:
                if len(value)<=len(previous):return p
                if not value.startswith(previous):raise ValueError('Captured byte prefix changed during getter replay')
            updated=replace(cached,**{field:value})
            self.observation=replace(self.observation,name=updated) if nested else updated
        raise ValueError('Inventory getter exceeded source operand budget')
