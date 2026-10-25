"""Construct our UI hidden, preserving the foreground application."""
import tkinter as tk
from app import Application
from routes import RouteStep

root = tk.Tk()
root.withdraw()
try:
    app = Application(root)
    from smoke_pet_ui import check_pet_ui
    check_pet_ui(app)
    from smoke_merchant_quick_ui import check_merchant_quick_ui
    check_merchant_quick_ui(app)
    from smoke_merchant_txt_export_ui import check_merchant_txt_export_ui
    check_merchant_txt_export_ui(app)
    from smoke_merchant_scan_ui import check_merchant_scan_ui
    check_merchant_scan_ui(app)
    from smoke_merchant_scan_loop_ui import check_merchant_scan_loop_ui
    check_merchant_scan_loop_ui(app)
    from smoke_merchant_scan_reply_ui import check_merchant_scan_reply_ui
    check_merchant_scan_reply_ui(app)
    from smoke_merchant_results_ui import check_merchant_results_ui
    check_merchant_results_ui(app)
    from smoke_merchant_cells_ui import check_merchant_cells_ui
    check_merchant_cells_ui(app)
    from smoke_flood_editor import check_flood_editor
    check_flood_editor(app)
    from smoke_flood_runtime import check_flood_runtime
    check_flood_runtime(app)
    from smoke_flood_selected import check_flood_selected
    check_flood_selected(app)
    from smoke_item_break_settings_ui import check_item_break_settings_ui
    check_item_break_settings_ui(app)
    from smoke_item_break_manual_ui import check_item_break_manual_ui
    check_item_break_manual_ui(app)
    from smoke_item_break_auto_ui import check_item_break_auto_ui
    check_item_break_auto_ui(app)
    from smoke_route_panel_ui import check_source_route_panel_ui
    check_source_route_panel_ui(app)
    from smoke_route_save_ui import check_source_route_save_ui
    check_source_route_save_ui(app)
    from smoke_route_load_ui import check_source_route_load_ui
    check_source_route_load_ui(app)
    from smoke_route_command_ui import check_source_route_command_ui
    check_source_route_command_ui(app)
    from smoke_route_advanced_ui import check_source_route_advanced_ui
    check_source_route_advanced_ui(app)
    from smoke_route_coordinate_ui import check_source_route_coordinate_ui
    check_source_route_coordinate_ui(app)
    from smoke_route_npc_ui import check_source_route_npc_ui
    check_source_route_npc_ui(app)
    from smoke_route_gate_ui import check_source_route_gate_ui
    check_source_route_gate_ui(app)
    from smoke_upgrade_editor_ui import check_upgrade_editor_ui
    check_upgrade_editor_ui(app)
    from smoke_upgrade_refresh_ui import check_upgrade_refresh_ui
    check_upgrade_refresh_ui(app)
    from smoke_upgrade_parameter_ui import check_upgrade_parameter_ui
    check_upgrade_parameter_ui(app)
    from smoke_upgrade_start_ui import check_upgrade_start_ui
    check_upgrade_start_ui(app)
    from smoke_upgrade_worker_ui import check_upgrade_worker_ui
    check_upgrade_worker_ui(app)
    from smoke_armor_start_ui import check_armor_start_ui
    check_armor_start_ui(app)
    from smoke_armor_worker_ui import check_armor_worker_ui
    check_armor_worker_ui(app)
    from smoke_quest_metadata_ui import check_quest_metadata_ui
    check_quest_metadata_ui(app)
    from smoke_quest_refresh_ui import check_quest_refresh_ui
    check_quest_refresh_ui(app)
    from smoke_quest_npc_filter_ui import check_quest_npc_filter_ui
    check_quest_npc_filter_ui(app)
    from smoke_quest_details_ui import check_quest_details_ui
    check_quest_details_ui(app)
    from smoke_quest_action_ui import check_quest_action_ui
    check_quest_action_ui(app)
    from smoke_control_settings_ui import check_control_settings_ui
    check_control_settings_ui(app)
    from smoke_genie_settings_ui import check_genie_settings_ui
    check_genie_settings_ui(app)
    from smoke_disconnect_settings_ui import check_disconnect_settings_ui
    check_disconnect_settings_ui(app)
    from smoke_dc_panel_ui import check_dc_panel_ui
    check_dc_panel_ui(app)
    from smoke_jail_selection_ui import check_jail_selection_ui
    check_jail_selection_ui(app)
    from smoke_protection_settings_ui import check_protection_settings_ui
    check_protection_settings_ui(app)
    from smoke_tp_protection_ui import check_tp_protection_ui
    check_tp_protection_ui(app)
    from smoke_transformation_ui import check_transformation_ui
    check_transformation_ui(app)
    from smoke_event_join_ui import check_event_join_ui
    check_event_join_ui(app)
    from smoke_allocation_panel_ui import check_allocation_panel_ui
    check_allocation_panel_ui(app)
    from smoke_ms_achievement_ui import check_ms_achievement_ui
    check_ms_achievement_ui(app)
    from smoke_monster_stone_ui import check_monster_stone_ui
    check_monster_stone_ui(app)
    from smoke_chat_skills_ui import check_chat_skills_ui
    check_chat_skills_ui(app)
    from smoke_chat_commands_ui import check_chat_commands_ui
    check_chat_commands_ui(app)
    from smoke_chat_party_ui import check_chat_party_ui
    check_chat_party_ui(app)
    from smoke_party_invitation_ui import check_party_invitation_ui
    check_party_invitation_ui(app)
    from smoke_follow_ui import check_follow_ui
    check_follow_ui(app)
    from smoke_name_lists import check_name_list_ui
    check_name_list_ui(app)
    from smoke_route_catalog import check_route_catalog_ui
    check_route_catalog_ui(app)
    from smoke_engine_route_inputs import check_engine_route_inputs
    check_engine_route_inputs(app)
    from smoke_sell_bank_route import check_sell_bank_route_ui
    check_sell_bank_route_ui(app)
    from smoke_buy_bank_route import check_buy_bank_route_ui
    check_buy_bank_route_ui(app)
    print('BUY bank-route UI passed: fresh failure count distinct from setup, delayed input/outer parent gates, BMerchant file only and no stale repeat handoff')
    print('SELL bank-route UI passed: lazy failure/route inputs, imported file held by outer-return gap, local simulator handoff, missing-file error without stale handoff')
    print('Engine route inputs passed: selected SELL/BUY Unicode and mining1254/UTF8 names, unknown provider retained, unselected panel branch skipped')
    print('All10 route catalogs UI passed: own directory -> actual combo choice -> .R import, persisted dynamic choices and failure isolation')
    print('Name-list panel passed: add/duplicate/empty/case, selected removal, isolated clear and profile roundtrip; own Unicode policy, no native actions')
    root.update_idletasks()
    count = 0
    def walk(parent=''):
        global count
        for item in app.tree.get_children(parent):
            count += 1
            walk(item)
    walk()
    assert count == 1037, count
    assert len(app.panel.main_tabs) == 18
    rendered_paths = set()
    for form in app.panel.forms:
        app.panel.form.set(form['path'])
        app.panel.render()
        rendered_paths.update(app.panel.widgets)
    assert len(rendered_paths) == 1037, len(rendered_paths)
    app.panel.form.set('frmMain')
    app.panel.render()
    for tab in app.panel.main_tabs:
        app.panel.section.set(tab['properties']['Caption'])
        app.panel.select_sections()
        notebook = app.panel.widgets['frmMain/MainTab']
        assert notebook.select() == str(app.panel.widgets[tab['path']])
    # Exercise the detail renderer for every captured node, including lists.
    for node in app.catalog:
        app.tree.selection_set(node['path'])
        app.select()
    app.search.set('AutoLoot')
    assert app.tree.get_children()
    app.simulate()
    assert app.sim_result.get().startswith('MP')
    assert len(app.sim_queue.records)==1 and len(app.sim_queue.records[0].payload)==30
    app.sim_actor.set(str(0x12345678));app.simulate()
    assert app.sim_queue.records[0].payload[6:8]==b'\x78\x56'
    assert app.sim_queue.records[0].payload[10:12]==b'\x78\x56'
    app.sim_connection.set(False);app.simulate()
    assert app.sim_queue.records==() and app.sim_queue_results[0].status=='not_enqueued'
    assert app.sim_result.get().startswith('MP')
    app.sim_connection.set(True);app.sim_actor.set('1');app.simulate()
    route = app.route_page
    route.use_panel_route_text.set(False) # Subsequent legacy fixtures supply an explicit manual name.
    route.steps = [RouteStep('Bekle', seconds=0), RouteStep('Koordinat', 12, 34)]
    route.refresh()
    assert len(route.list.get_children()) == 2
    route.start()
    route.tick()
    route.tick()
    route.tick()
    route.tick()
    route.distance.set('2')
    route.tick()
    route.tick()
    assert route.runner.reason == 'Tamamlandı'
    route.stop()
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as source_route_temp:
        source_path=Path(source_route_temp)/'owned.R'
        source_path.write_bytes(b'[Count]\nValue=1\n[ROUTE]\nISLEM0=Bekle\nSub10=0\n')
        imported=route.load_source_path(str(source_path))
        assert imported.complete and imported.changed and route.steps==[RouteStep('Bekle',seconds=0)]
        route.start()
        for _ in range(4):route.tick()
        assert route.runner.reason=='Tamamlandı'
        preserved=list(route.steps)
        zero_path=Path(source_route_temp)/'zero.R';zero_path.write_bytes(b'[Count]\nValue=0\n')
        assert not route.load_source_path(str(zero_path)).changed and route.steps==preserved
        bad_path=Path(source_route_temp)/'bad.R';bad_path.write_bytes(b'[Count]\nValue=1\n[ROUTE]\nISLEM0=Unknown\n')
        assert not route.load_source_path(str(bad_path)).complete and route.steps==preserved
        from supply_configuration import GROUP as SUPPLY_GROUP,RESPAWN as RETURN_GROUP
        from supply_routes import LIST_PATHS as ROUTE_LIST_PATHS
        import copy
        route_values_before=dict(app.values);route_lists_before=copy.deepcopy(app.lists)
        cycle_path=Path(source_route_temp)/'cycle.R'
        cycle_path.write_bytes(b'[Count]\nValue=1\n[ROUTE]\nISLEM0=Koordinat\nSub10=12\nSub20=34\n')
        app.profiles.update(app.values,SUPPLY_GROUP+'chChangeSupplyRoute',True)
        app.lists[ROUTE_LIST_PATHS['supply']]=[{'caption':'missing.R'},{'caption':'cycle.R'}]
        route.supply_directory.set(source_route_temp);route.supply_manual.set('owned.R')
        assert route.load_panel_route().ready
        assert route.panel_route_choice.status=='manual_route_fallback' and route.supply_route_state.supply_counter==1
        assert route.load_panel_route().ready and route.panel_route_choice.used_cyclic
        assert route.steps==[RouteStep('Koordinat',12,34)] and route.supply_route_state.supply_counter==2
        route.supply_kind.set('Dönüş')
        app.profiles.update(app.values,RETURN_GROUP+'chChangeReturnRoute',True)
        app.lists[ROUTE_LIST_PATHS['return']]=[{'caption':'cycle.R'}]
        assert route.load_panel_route().ready and route.supply_route_state.return_counter==1
        assert route.supply_route_state.supply_counter==2
        route.supply_manual.set('owned.R')
        main_counters=route.supply_route_state
        for kind in ('Sell Merchant','Buy Merchant','AntiCR','Karşı ırk','Notice','PM kontrol','Relog'):
            route.supply_kind.set(kind)
            assert route.load_panel_route().ready and route.panel_route_choice.status=='global_route_choice'
            assert route.supply_route_state==main_counters
        from global_route_choices import MINE_CHANGE_PATH,MINE_LIST_PATH
        mine_check=Path(source_route_temp)/'mine-check';mine_check.mkdir()
        (mine_check/'cycle.R').write_bytes(b'not imported: selection checks existence only')
        app.profiles.update(app.values,MINE_CHANGE_PATH,True)
        app.lists[MINE_LIST_PATH]=[{'caption':'cycle.R','checked':False}]
        route.supply_kind.set('Maden');route.mine_check_directory.set(str(mine_check))
        assert route.load_panel_route().ready and route.panel_route_choice.status=='mining_cyclic_route_choice'
        assert route.steps==[RouteStep('Koordinat',12,34)] and route.mine_route_counter==1
        assert route.supply_route_state==main_counters
        (mine_check/'cycle.R').unlink()
        assert route.load_panel_route().ready and route.panel_route_choice.status=='mining_manual_fallback'
        assert route.steps==[RouteStep('Bekle',seconds=0)] and route.mine_route_counter==1
        app.profiles.update(app.values,MINE_CHANGE_PATH,False);route.mine_check_directory.set('')
        assert route.load_panel_route().ready and route.mine_route_counter==1
        route.supply_kind.set('Tedarik')
        app.profiles.update(app.values,SUPPLY_GROUP+'chChangeSupplyRoute',False)
        for name in ('zero.R','not-found.R',''):
            route.supply_manual.set(name);route.start();assert route.runner.active
            result=route.load_panel_route()
            assert result.stop_required and not route.runner.active
        app.values.clear();app.values.update(route_values_before)
        app.lists.clear();app.lists.update(route_lists_before)
    route.stop()
    assert not route.runner.active
    route.steps = [RouteStep('Town'), RouteStep('Gate Skill', parameter1='5'),
                   RouteStep('NPC', parameter1='Sundries', parameter2='Al')]
    route.refresh()
    route.npc_complete.set(True)
    route.start()
    for _ in range(16):
        route.tick(1000)
    assert route.runner.reason == 'Tamamlandı'
    route.stop()
    for name in app.mining_page.routes:
        app.mining_page.choice.set(name)
        app.mining_page.render()
    for case in app.engine_page.CASES:
        app.engine_page.case.set(case)
        app.engine_page.reset()
        for _ in range(4):
            app.engine_page.tick()
        app.engine_page.tick(60000)
        assert 'Deneme değeri geçersiz' not in app.engine_page.output.get('1.0', 'end'), case
        if case=='NPC Onarım':
            assert len(app.engine_page.repair_last.queue_payloads)==1
            assert app.engine_page.input_labels['hp'].cget('text')=='Dayanıklılık'
        if case=='NPC Enchant':
            assert len(app.engine_page.enchant_last.queue_payloads)==1
            assert app.engine_page.input_labels['hp'].cget('text')=='Seviye'
    engine=app.engine_page
    # BUY setup uses observed inventory and post-preparation rows, rather than
    # the previous unconditional synthetic setup_result=0.
    engine.case.set('Buy Merchant');engine.ready.set(True);engine.full.set(False)
    merchant_original={key:engine.inputs[key].get() for key in ('item_id','quantity','price')}
    for key,value in (('item_id','1'),('quantity','2'),('price','100')):engine.inputs[key].set(value)
    engine.buy_merchant_fixture.set(False);engine.reset()
    engine.tick(1);engine.tick(1);engine.tick(61000)
    assert engine.merchant.phase==2 and not engine.merchant.setup_seen
    assert 'needs_adapter' in engine.output.get('1.0','end')
    engine.buy_merchant_fixture.set(True);engine.buy_merchant_coins.set('1000')
    engine.buy_merchant_free.set('12');engine.buy_merchant_threshold.set('0');engine.reset()
    engine.tick(1);engine.tick(1);engine.tick(61000)
    assert engine.merchant.phase==2 and engine.merchant.setup_seen
    engine.tick(1);assert engine.merchant.phase==3
    engine.tick(1);engine.tick(1);engine.tick(1)
    assert engine.merchant.phase==5
    assert engine.merchant_open_last.complete and len(engine.merchant_open_queue.records)==2
    assert [r.delay_dword for r in engine.merchant_open_queue.records]==[0,1000]
    assert engine.merchant_open_queue.records[0].payload==b'\x68\x21'
    engine.full.set(True);engine.tick(1)
    assert engine.merchant.phase==0 and engine.merchant.restarting
    engine.full.set(False);engine.buy_merchant_coins.set('199');engine.reset()
    engine.tick(1);engine.tick(1);engine.tick(61000)
    assert not engine.merchant.active and engine.merchant.reason=='setup_result'
    assert 'Deneme değeri geçersiz' not in engine.output.get('1.0','end')
    engine.buy_merchant_coins.set('1000');engine.buy_merchant_threshold.set('4294967295')
    engine.buy_merchant_free.set('1');engine.reset()
    engine.tick(1);engine.tick(1);engine.tick(61000);engine.tick(1);engine.tick(1);engine.tick(1)
    assert engine.merchant.phase==5
    engine.full.set(True);engine.tick(1)
    assert engine.merchant.phase==5 and engine.merchant.active # signed threshold=-1
    engine.full.set(False);engine.buy_merchant_free.set('12');engine.buy_merchant_threshold.set('0')
    engine.buy_merchant_coins.set('1000');engine.ready.set(True);engine.reset()
    engine.tick(1);engine.tick(1);engine.tick(61000);engine.tick(1)
    assert engine.merchant.phase==3
    engine.ready.set(False);engine.tick(1)
    initial_open_tick=engine.now_ms
    assert engine.merchant.phase==3 and not engine.merchant_open_frame_last.complete
    assert engine.merchant_open_frame_last.prospective_state.pending_byte==1
    assert engine.merchant_open_frame_last.prospective_state.pending_stamp_qword==initial_open_tick
    engine.tick(2000)
    assert engine.merchant.phase==3 and engine.merchant_open_queue.records==()
    engine.ready.set(True);engine.tick(1)
    assert engine.merchant.phase==4 and engine.merchant.phase_ms==initial_open_tick
    assert engine.merchant_open_frame_last.calls.count(('GetTickCount',))==1
    assert len(engine.merchant_open_queue.records)==2
    buy_path='frmMain/MainTab/sheetBuyMerchant/GroupBox55/LwAutoBuyMerchant'
    original_buy_rows=app.lists[buy_path]
    app.lists[buy_path]=[{'caption':'4294967297','subitems':['Ignored name','2','4.294.967.297'],'checked':False}]
    engine.use_class_panel.set(True);engine.buy_merchant_coins.set('2');engine.reset()
    engine.tick(1);engine.tick(1);engine.tick(91000)
    assert engine.merchant.settings.extra_wait_seconds==30
    plan=engine.merchant.last_buy_setup_plan
    assert engine.merchant.setup_seen and plan.complete and plan.result_dword==0
    assert plan.preparation_plan.state.records[0].price_qword==0x100000001
    assert plan.preparation_plan.state.records[0].item_dword==1 and plan.row_costs==((0,2),)
    engine.tick(1);engine.tick(1)
    assert engine.merchant.phase==4 and engine.merchant_open_last.complete
    assert engine.merchant_open_queue.records[-1].payload==bytes.fromhex('68220101000000020001000000')
    assert engine.merchant_open_state.accumulated_qword==2
    app.lists[buy_path]=[{'caption':'1','subitems':['Ignored name','2','1.2'],'checked':False}]
    engine.reset();engine.tick(1);engine.tick(1);engine.tick(91000)
    assert not engine.merchant.setup_seen and engine.merchant.phase==2
    assert not engine.merchant.last_buy_setup_plan.preparation_plan.complete
    assert 'StrToInt64' in engine.merchant.last_buy_setup_plan.missing
    app.lists[buy_path]=original_buy_rows;engine.use_class_panel.set(False)
    engine.buy_merchant_coins.set('1000');engine.buy_merchant_fixture.set(False)
    for key,value in merchant_original.items():engine.inputs[key].set(value)
    print('BUY setup UI passed: explicit observations, cost200 with budget1000/199, full inventory restart and signed threshold; no game actions')
    engine.case.set('NPC Onarım');engine.ready.set(False);engine.reset()
    for _ in range(4):engine.tick()
    assert engine.repair_last.status=='waiting_ack'
    engine.ready.set(True);engine.tick()
    assert engine.repair_last.returned_phase==1
    engine.case.set('NPC Enchant');engine.inputs['item_id'].set('4');engine.reset()
    for _ in range(16):engine.tick()
    assert engine.enchant_last.returned_phase==8
    engine.case.set('NPC Satış');engine.inputs['item_id'].set('1');engine.ready.set(True);engine.reset()
    for _ in range(60):engine.tick()
    assert engine.sale_state.fields[0x654]==43
    assert engine.sale_state.batch==()
    assert engine.sale_plan_count==2
    engine.tick();assert engine.sale_plan_count==2
    engine.ready.set(False);engine.reset()
    for _ in range(45):engine.tick()
    assert engine.sale_state.fields[0x654]==43
    assert engine.sale_plan_count==0
    assert 'Deneme değeri geçersiz' not in engine.output.get('1.0','end')
    engine.case.set('NPC Satın Alma');engine.ready.set(True);engine.full.set(False)
    for name,value in {'hp':0,'hp_max':100,'mp':100,'threshold':1,'quantity':5,'price':1,'distance':1}.items():
        engine.inputs[name].set(str(value))
    engine.reset()
    for _ in range(6):engine.tick()
    assert engine.buy_state.fields[0x690]==2
    assert engine.buy_state.batch==()
    assert engine.buy_plan_count==1
    engine.tick();assert engine.buy_plan_count==1
    # The requested four additional items reach the weight limit exactly: skip.
    engine.inputs['hp_max'].set('4');engine.reset()
    for _ in range(6):engine.tick()
    assert engine.buy_state.fields[0x690]==2 and engine.buy_plan_count==0
    engine.inputs['hp_max'].set('100');engine.inputs['mp'].set('3');engine.reset()
    for _ in range(6):engine.tick()
    assert engine.buy_state.fields[0x690]==2 and engine.buy_plan_count==0
    engine.ready.set(False);engine.inputs['mp'].set('100');engine.reset()
    for _ in range(6):engine.tick()
    assert engine.buy_state.fields[0x690]==2 and engine.buy_plan_count==0
    assert 'Deneme değeri geçersiz' not in engine.output.get('1.0','end')
    engine.case.set('Upgrade');engine.reset()
    assert engine.input_labels['hp'].cget('text')=='HP'
    assert not engine.enchant_zone_choice.winfo_ismapped()
    # Panel milliseconds and checked captions override only the linked trial.
    from upgrade_configuration import WAIT_PATH as UPGRADE_WAIT,ANVIL_PATH as UPGRADE_ANVIL,LIST_PATH as UPGRADE_LIST,SCROLL_PATH as UPGRADE_SCROLL
    import copy
    upgrade_saved_values=copy.deepcopy(app.values);upgrade_saved_lists=copy.deepcopy(app.lists)
    upgrade_saved_wait=engine.inputs['wait'].get()
    app.profiles.update(app.values,UPGRADE_WAIT,'1500')
    app.profiles.update(app.values,UPGRADE_ANVIL,'42')
    app.lists[UPGRADE_LIST]=[{'caption':'11','subitems':['999'],'checked':True},
                             {'caption':'invalid','subitems':[],'checked':False},
                             {'caption':'22','subitems':[],'checked':True}]
    engine.use_class_panel.set(True);engine.ready.set(True)
    engine.inputs['wait'].set('999');engine.upgrade_scroll_fixture.set(False)
    app.lists[UPGRADE_LIST][0]['caption']='invalid selected caption'
    engine.reset();engine.tick()
    assert not engine.initialized and engine.now_ms==0 and engine.upgrade.state==0
    assert engine.upgrade_start_plan.prospective_state.queue==()
    assert 'fresh004073a0' in engine.upgrade_start_plan.missing
    engine.upgrade_scroll_fixture.set(True);engine.reset();engine.tick()
    assert not engine.initialized and 'caption outside local decimal' in engine.upgrade_start_plan.missing
    assert engine.upgrade_start_plan.prospective_state.scroll_index==2
    app.lists[UPGRADE_LIST][0]['caption']='11'
    engine.upgrade_scroll_fixture.set(True);engine.reset();engine.tick()
    assert engine.upgrade_start_plan.complete and engine.upgrade.source_scroll_index==2
    assert engine.upgrade.interval_ms==1500 and engine.upgrade.anvil_id==42
    assert engine.upgrade.queue==(11,22)
    engine.tick();assert engine.upgrade.queue==(22,)
    assert engine.upgrade.source_clock and engine.upgrade.queue_stamp_qword==2002
    assert len(engine.upgrade_execution.queue.records)==1
    upgrade_record=engine.upgrade_execution.queue.records[0]
    assert len(upgrade_record.payload)==57 and upgrade_record.created_tick==2001
    assert upgrade_record.payload[11]==11 and upgrade_record.payload[16]==2
    assert int.from_bytes(upgrade_record.payload[7:11],'little')==int(engine.inputs['item_id'].get())
    assert int.from_bytes(upgrade_record.payload[12:16],'little')==0x10203040
    engine.ready.set(False);engine.tick();engine.tick()
    assert engine.upgrade.queue==(22,)
    engine.ready.set(True);engine.tick();assert engine.upgrade.queue==()
    engine.tick();engine.tick();assert engine.upgrade.reason=='queue_empty'
    assert len(engine.upgrade_execution.queue.records)==2
    engine.upgrade_queue_gate.set('0');engine.reset();engine.tick(1500)
    assert engine.upgrade.queue==(22,) and engine.upgrade_execution.queue.records==()
    assert engine.upgrade_execution_last.queue_decision.status=='not_enqueued'
    engine.upgrade_queue_gate.set('1')
    app.profiles.update(app.values,UPGRADE_WAIT,'-1')
    engine.reset();engine.tick(0)
    assert engine.upgrade.interval_ms==0xffffffff and engine.upgrade.queue==(22,)
    assert engine.upgrade.queue_stamp_qword==2
    engine.upgrade_scroll_fixture.set(True);engine.upgrade_scroll_slot.set('27')
    engine.ready.set(False);engine.reset();engine.tick(0)
    assert engine.upgrade.source_scroll_index==27 and engine.upgrade.queue==(11,22)
    assert engine.upgrade.scroll_lookup_plan.visited_slots==tuple(range(14,42))
    engine.upgrade_scroll_slot.set('-1');engine.reset();engine.tick(0)
    assert engine.upgrade.source_scroll_index==-1 and engine.upgrade.reason=='scroll_unavailable'
    assert engine.upgrade.queue==(11,22)
    engine.upgrade_scroll_fixture.set(False);engine.ready.set(True)
    app.profiles.update(app.values,UPGRADE_SCROLL,-1)
    engine.reset();engine.tick()
    assert not engine.initialized and engine.now_ms==0
    assert 'combo Text unavailable' in engine.output.get('1.0','end')
    app.values.clear();app.values.update(upgrade_saved_values)
    app.lists.clear();app.lists.update(upgrade_saved_lists)
    engine.inputs['wait'].set(upgrade_saved_wait)
    engine.use_class_panel.set(False);engine.ready.set(True);engine.reset()
    armor_saved_inputs={k:v.get() for k,v in engine.inputs.items()}
    armor_saved_slot=engine.upgrade_scroll_slot.get()
    engine.case.set('Armor Alımı');engine.upgrade_scroll_fixture.set(False);engine.reset();engine.tick(203)
    assert not engine.initialized and engine.now_ms==0
    engine.upgrade_scroll_fixture.set(True);engine.upgrade_scroll_slot.set('3')
    engine.inputs['price'].set('9');engine.inputs['item_id'].set('0')
    engine.inputs['threshold'].set('1');engine.inputs['distance'].set('9')
    engine.upgrade_queue_gate.set('1');engine.armor_second_gate.set('1')
    engine.ready.set(True);engine.full.set(False);engine.reset()
    for _ in range(43):engine.tick(203)
    assert (engine.upgrade.armor_attempts,engine.upgrade.state)==(43,0)
    assert len(engine.upgrade_execution.queue.records)==86
    first_armor=engine.upgrade_execution.queue.records[0]
    assert len(first_armor.payload)==20 and first_armor.created_tick==204
    assert first_armor.payload[15:20]==bytes.fromhex('0301000001')
    assert int.from_bytes(first_armor.payload[11:15],'little')==0x0bfb0829
    assert engine.armor_start_plan.armed and engine.upgrade.armor_source_fields[0x5c]==1
    second_armor=engine.upgrade_execution.queue.records[1]
    assert second_armor.payload==b'\x6a\x02' and second_armor.created_tick==205 and second_armor.delay_dword==100
    engine.tick();assert len(engine.upgrade_execution.queue.records)==86
    engine.ready.set(False);engine.reset();engine.tick(203)
    assert engine.upgrade.armor_attempts==0 and engine.upgrade_execution.queue.records==()
    assert len(engine.upgrade_execution_last.prospective_queue.records)==2
    engine.ready.set(True);engine.tick(0)
    assert engine.upgrade.armor_attempts==1 and len(engine.upgrade_execution.queue.records)==2
    engine.upgrade_queue_gate.set('0');engine.armor_second_gate.set('1');engine.reset();engine.tick(203)
    assert len(engine.upgrade_execution.queue.records)==1 and engine.upgrade_execution.queue.records[0].payload==b'\x6a\x02'
    engine.upgrade_queue_gate.set('1');engine.armor_second_gate.set('0');engine.reset();engine.tick(203)
    assert len(engine.upgrade_execution.queue.records)==1 and len(engine.upgrade_execution.queue.records[0].payload)==20
    engine.armor_second_gate.set('1');engine.full.set(True);engine.reset();engine.tick(203)
    assert not engine.initialized and engine.armor_start_plan.status=='bag_full'
    assert engine.upgrade_execution is None
    engine.full.set(False);engine.reset();engine.tick(203);engine.full.set(True);engine.tick(203)
    assert engine.upgrade.reason=='armor_gate' and len(engine.upgrade_execution.queue.records)==2
    engine.full.set(False);engine.upgrade_scroll_slot.set('-1');engine.reset();engine.tick(203)
    assert engine.upgrade_execution.queue.records[0].payload[15]==255
    assert 'Deneme değeri geçersiz' not in engine.output.get('1.0','end')
    from armor_start import COMBO_PATH as ARMOR_COMBO_PATH
    armor_saved_combo=app.values[ARMOR_COMBO_PATH]
    engine.use_class_panel.set(True);app.profiles.update(app.values,ARMOR_COMBO_PATH,6)
    engine.reset();engine.tick(203)
    assert int.from_bytes(engine.upgrade_execution.queue.records[0].payload[11:15],'little')==0x0e5d6229
    assert engine.upgrade_execution.queue.records[0].payload[19]==6
    app.profiles.update(app.values,ARMOR_COMBO_PATH,5);engine.reset();engine.tick(203)
    assert not engine.initialized and engine.armor_start_plan.status=='item_missing'
    assert not any(c[0]=='GetItemIndex:second' for c in engine.armor_start_plan.calls)
    app.profiles.update(app.values,ARMOR_COMBO_PATH,armor_saved_combo);engine.use_class_panel.set(False)
    engine.inputs['price'].set('0');engine.reset();engine.tick(203)
    assert not engine.initialized and engine.armor_start_plan.status=='npc_missing'
    for k,v in armor_saved_inputs.items():engine.inputs[k].set(v)
    engine.upgrade_scroll_slot.set(armor_saved_slot);engine.upgrade_scroll_fixture.set(False)
    engine.upgrade_queue_gate.set('1');engine.armor_second_gate.set('1');engine.ready.set(True);engine.full.set(False)
    engine.case.set('Eylem Kuyruğu');engine.ready.set(True);engine.reset()
    assert engine.upgrade_scroll_controls.winfo_manager()==''
    assert engine.armor_extra.winfo_manager()==''
    engine.tick()
    assert len(engine.action_queue.records)==3
    assert engine.action_queue_send_plans==0
    engine.tick()
    assert len(engine.action_queue.records)==1 and engine.action_queue_send_plans==2
    engine.tick()
    assert len(engine.action_queue.records)==0 and engine.action_queue_send_plans==3
    engine.tick();assert engine.action_queue_send_plans==3
    assert 'Sunucu onayı' in engine.output.get('1.0','end')
    engine.reset();engine.tick();engine.ready.set(False);engine.tick();engine.tick()
    assert engine.action_queue_send_plans==0 and engine.action_queue_drops==3
    assert len(engine.action_queue.records)==0
    engine.reset();engine.tick()
    assert len(engine.action_queue.records)==0 and engine.action_queue_drops==0
    assert 'Deneme değeri geçersiz' not in engine.output.get('1.0','end')
    # Derived class UI effects must reach both profile values and visible radio state.
    from rogue_attack import BOW_ROWS
    normal='frmMain/MainTab/SheetBot/GroupBox34/rdUseNormalSkill'
    arrow='frmMain/MainTab/SheetJob/pnlRogue/GroupBox46/charrowrain'
    group=next(g for g in app.profiles.radio_groups.values() if normal in g)
    sibling=next(p for p in group if p!=normal)
    saved_values=dict(app.values)
    app.panel.set_value(sibling,True);app.panel.set_value(arrow,True)
    engine.use_class_panel.set(False);engine.attack_flags('rogue',BOW_ROWS)
    assert app.values[sibling] and not app.values[normal]
    engine.use_class_panel.set(True);engine.attack_flags('rogue',BOW_ROWS)
    assert app.values[normal] and not app.values[sibling]
    assert app.panel.radio_variables[normal.rsplit('/',1)[0]].get()==normal
    app.panel.set_value(arrow,False);engine.attack_flags('rogue',BOW_ROWS)
    assert app.values[normal] # Source emits no inverse effect when Arrow Rain is off.
    app.values.clear();app.values.update(saved_values);app.panel.render()
    engine.use_class_panel.set(False)
    # Support settings must come from source panel fields rather than demo thresholds.
    import json
    from pathlib import Path
    schema=json.loads((Path(__file__).parent/'class_configuration_map.json').read_text(encoding='utf-8'))
    saved_values=dict(app.values)
    def source_field(job,kind,offset,value):
        path=next(p for p,spec in schema[job][kind].items()
                  if (spec['offset'] if isinstance(spec,dict) else spec)==offset)
        app.profiles.update(app.values,path,value)
    for name,value in {'hp':20,'hp_max':100,'mp':1100,'threshold':1,'item_id':1}.items():engine.inputs[name].set(str(value))
    engine.ready.set(True);engine.use_class_panel.set(True)
    source_field('priest','booleans',0xc0,True);source_field('priest','booleans',0xcc,False)
    source_field('priest','integers',0xc4,'40');source_field('priest','combos',0xc8,3)
    engine.case.set('Priest');engine.reset()
    for _ in range(3):engine.tick()
    assert engine.support_settings.self_threshold==40 and engine.support_settings.self_skill_id==500
    assert engine.support_last.intent.skill_id==500
    source_field('rogue','booleans',0,True);source_field('rogue','integers',4,'25');source_field('rogue','integers',8,'1500')
    engine.case.set('Rogue Minor');engine.reset();engine.tick()
    assert engine.support_last.status=='waiting'
    engine.tick();assert engine.support_last.intent is not None
    assert engine.support_settings.interval_ms==1500
    source_field('kurian','booleans',0xdb,True);source_field('kurian','integers',0xdc,'19')
    engine.case.set('Kurian');engine.reset();engine.tick()
    assert engine.support_last.status=='no_action'
    source_field('kurian','integers',0xdc,'20');engine.tick()
    assert engine.support_last.intent is not None
    source_field('mage','booleans',3,True);source_field('mage','integers',4,'45')
    source_field('mage','booleans',8,False);source_field('mage','texts',12,'Exact name')
    engine.case.set('Mage TP');engine.reset();engine.tick()
    assert engine.support_settings.threshold==45 and engine.support_settings.target_name=='Exact name'
    assert engine.support_last.intent is None # Party candidate age must exceed2499ms.
    engine.tick();engine.tick()
    assert engine.support_last.intent is not None
    source_field('warrior','booleans',0x198,True)
    for offset,value in ((0x1a0,'60'),(0x1a4,'2'),(0x1a8,'3')):source_field('warrior','integers',offset,value)
    for offset in (0x19a,0x19b,0x19c,0x19d):source_field('warrior','booleans',offset,offset==0x19d)
    engine.case.set('Warrior Provoke');engine.reset();engine.tick()
    assert engine.provoke_last.status=='wait_start_delay'
    engine.tick();assert engine.provoke_last.status=='wait_skill_delay'
    engine.tick();assert engine.provoke_last.status=='local_return_nonzero'
    assert engine.provoke_state.used[3]
    assert (engine.provoke_settings.window_seconds,engine.provoke_settings.start_delay_seconds,
            engine.provoke_settings.skill_delay_seconds)==(60,2,3)
    source_field('warrior','booleans',0x198,False);engine.tick()
    assert engine.provoke_last.status=='caller_disabled'
    import copy
    saved_lists=copy.deepcopy(app.lists)
    for path,offsets in schema['rogue']['lists'].items():
        for index,offset in enumerate(offsets):
            if offset in (0x89,0x91):app.lists[path][index]['checked']=offset==0x89
    source_field('rogue','integers',0x10,'4');source_field('rogue','integers',0x14,'0')
    bot='frmMain/MainTab/SheetBot/GroupBox34/'
    app.profiles.update(app.values,bot+'rdUseNormalSkill',True)
    app.profiles.update(app.values,bot+'GroupBox35/chNManuelAtackSpeed',False)
    engine.inputs['distance'].set('5');engine.case.set('Rogue Çoklu');engine.reset();engine.tick(2000)
    assert engine.volley_ranges.triple==4
    assert not any(call[0]=='004de710' for call in engine.volley_last.calls)
    source_field('rogue','integers',0x10,'5');engine.reset();engine.tick(2000)
    assert any(call[0]=='004de710' for call in engine.volley_last.calls)
    source_field('rogue','integers',0x18,'4')
    from combo_configuration import COMBO_PANEL_INPUTS
    for path,value in zip(COMBO_PANEL_INPUTS,(True,False,False)):app.profiles.update(app.values,path,value)
    engine.inputs['mp'].set('1000');engine.case.set('Rogue Alternatif Yay');engine.reset();engine.tick()
    assert engine.alternate_bow_ranges.combo==4 and engine.alternate_bow_last.category!=2
    source_field('rogue','integers',0x18,'5');engine.reset();engine.tick()
    assert engine.alternate_bow_last.category==2 and engine.alternate_bow_last.skill_number==0x203
    assert engine.alternate_bow_last.local_writes==() and not engine.alternate_bow_last.independently_verified
    engine.ready.set(True);engine.case.set('Rogue Combo Zinciri');engine.reset();engine.tick(1000)
    assert engine.rogue_chain_last.head.calls[-1]=='004db864'
    assert engine.rogue_chain_last.combo.selector.skill_number==0x203
    assert engine.rogue_chain_state.combo.stage==1
    engine.tick(500);assert engine.rogue_chain_state.combo.stage==3
    engine.tick(1);assert engine.rogue_chain_state.combo.stage==4
    engine.tick(4);assert engine.rogue_chain_state.combo.stage==4
    engine.tick(1);assert engine.rogue_chain_state.combo.stage==5
    engine.tick(5);assert engine.rogue_chain_state.combo.stage==6
    engine.tick(488);assert engine.rogue_chain_state.combo.stage==6
    engine.tick(1);assert engine.rogue_chain_state.combo.stage==7
    assert engine.rogue_chain_last.combo.selector.local_writes==()
    engine.tick(1250);assert engine.rogue_chain_state.combo.stage==0
    engine.ready.set(False);engine.tick();assert engine.rogue_chain_last.combo is None
    engine.ready.set(True)
    from attack_lock import AttackLockState
    engine.reset();engine.attack_lock_state=AttackLockState(1,600,0)
    engine.tick(599)
    assert engine.attack_lock_last.status=='wait_lock_duration' and engine.rogue_chain_last.combo is None
    engine.tick(1)
    assert engine.attack_lock_last.status=='lock_cleared' and engine.rogue_chain_state.combo.stage==1
    assert engine.attack_lock_state==AttackLockState(1,600,0) # Selector sets BYTE only; does not refresh duration/start.
    engine.tick(1)
    assert engine.attack_lock_last.status=='lock_cleared' and engine.rogue_chain_state.combo.stage==1
    # W/S are independent panel controls, not hardcoded runtime1/0.
    app.profiles.update(app.values,COMBO_PANEL_INPUTS[0],False)
    app.profiles.update(app.values,COMBO_PANEL_INPUTS[1],True)
    engine.inputs['distance'].set('0');engine.reset();engine.tick(1000);engine.tick(460);engine.tick(1)
    assert engine.combo_config.w_byte==0 and engine.combo_config.s_byte==1
    assert engine.rogue_chain_last.combo.calls[-1]==('00465f30',(2,))
    app.profiles.update(app.values,COMBO_PANEL_INPUTS[0],True)
    engine.reset();engine.tick(1000);engine.tick(460);engine.tick(1)
    assert engine.combo_config.w_combo and engine.combo_config.s_combo
    assert engine.rogue_chain_state.combo.pattern_counter==1
    assert engine.rogue_chain_last.combo.calls[-1]==('00465f30',(2,))
    for path,value in zip(COMBO_PANEL_INPUTS,(True,False,False)):app.profiles.update(app.values,path,value)
    engine.inputs['distance'].set('5')
    engine.case.set('Rogue Çoklu');engine.reset()
    app.profiles.update(app.values,bot+'GroupBox35/chNManuelAtackSpeed',True)
    app.profiles.update(app.values,bot+'GroupBox35/txtNiManuelAtackSpeed','2000')
    engine.reset();engine.tick()
    assert engine.bot_combat.attack_interval_ms==2000
    assert not any(call[0]=='004de710' for call in engine.volley_last.calls)
    engine.tick();assert any(call[0]=='004de710' for call in engine.volley_last.calls)
    app.profiles.update(app.values,bot+'GroupBox35/txtNAtackDistance','4')
    engine.case.set('Priest Saldırı');engine.reset();engine.tick()
    assert engine.attack_last.status=='out_of_range'
    assert engine.bot_combat.attack_range==4
    app.profiles.update(app.values,bot+'GroupBox35/txtNAtackDistance','50')
    engine.inputs['distance'].set('46');engine.case.set('Mage Saldırı');engine.reset();engine.tick()
    assert engine.attack_last.status=='out_of_range' # Source Mage cap45 remains.
    app.profiles.update(app.values,bot+'rdUseLegalSkill',True)
    app.profiles.update(app.values,bot+'GroupBox38/txtLAtackDistance','3')
    app.profiles.update(app.values,bot+'GroupBox38/chLManuelAtackSpeed',False)
    engine.inputs['distance'].set('5');engine.case.set('Warrior Saldırı');engine.reset();engine.tick()
    assert engine.attack_last.status=='out_of_range'
    assert (engine.bot_combat.legal_mode,engine.bot_combat.attack_range,engine.bot_combat.attack_interval_ms)==(True,3,250)
    app.lists.clear();app.lists.update(saved_lists)
    app.values.clear();app.values.update(saved_values);app.panel.render();engine.use_class_panel.set(False)
    assert 'Deneme değeri geçersiz' not in engine.output.get('1.0','end')
    saved_values=dict(app.values)
    engine.case.set('Sınıf Ailesi');engine.use_class_panel.set(False)
    engine.family_runtime.set('Panel adayı');engine.family_normal_guard.set('0');engine.ready.set(True);engine.reset()
    assert engine.family_controls.winfo_manager()=='grid'
    expected_heads={'mage':('0049bad0','0049b928'),'rogue':('004de490','004dc544'),
                    'priest':('004d1be4','004d1d88'),'warrior':('00501b64','00501dbc'),
                    'kurian':('00471954','00471a28')}
    for job,pair in expected_heads.items():
        engine.family_job.set(job)
        for index,radio in enumerate(('rdUseNormalSkill','rdUseLegalSkill')):
            app.profiles.update(app.values,bot+radio,True);engine.tick()
            assert engine.family_last.selection.head==pair[index]
            assert engine.family_last.result is not None
    engine.family_job.set('mage')
    app.profiles.update(app.values,bot+'rdUseLegalSkill',True)
    app.profiles.update(app.values,bot+'GroupBox35/chNManuelAtackSpeed',False)
    app.profiles.update(app.values,bot+'GroupBox38/chLManuelAtackSpeed',False)
    engine.family_runtime.set('0');engine.tick()
    assert engine.family_last.selection.family=='normal' and engine.family_active.attack_interval_ms==1250
    assert app.values[bot+'rdUseLegalSkill'] # Runtime override does not rewrite panel radio.
    app.profiles.update(app.values,bot+'rdUseNormalSkill',True)
    engine.family_runtime.set('255');engine.tick()
    assert engine.family_last.selection.family=='legal' and engine.family_active.attack_interval_ms==250
    engine.family_runtime.set('Panel adayı');engine.family_normal_guard.set('6');engine.tick()
    assert engine.family_last.selection.status=='blocked' and engine.family_last.result is None
    app.profiles.update(app.values,bot+'rdUseLegalSkill',True);engine.tick()
    assert engine.family_last.selection.family=='legal' and engine.family_last.result is not None
    before=(dict(engine.family_runner.normal_states),dict(engine.family_runner.legal_states))
    engine.ready.set(False);engine.tick()
    assert engine.family_last.result is None
    assert (engine.family_runner.normal_states,engine.family_runner.legal_states)==before
    app.values.clear();app.values.update(saved_values);app.panel.render()
    engine.ready.set(True);engine.family_runtime.set('Panel adayı');engine.family_normal_guard.set('0')
    engine.case.set('Upgrade');engine.reset();assert engine.family_controls.winfo_manager()==''
    assert 'Deneme değeri geçersiz' not in engine.output.get('1.0','end')
    from target_configuration import MODE_PATHS,LIST_PATH,POOL_PATHS
    saved_values=dict(app.values);saved_lists=copy.deepcopy(app.lists)
    engine.case.set('Hedef Seçimi');engine.ready.set(True);engine.target_pool.set('0')
    engine.inputs['item_id'].set('11');engine.inputs['distance'].set('3')
    app.profiles.update(app.values,MODE_PATHS[2],True)
    app.profiles.update(app.values,bot+'rdUseNormalSkill',True)
    app.profiles.update(app.values,bot+'GroupBox35/txtNMobSelectDistance','4')
    app.profiles.update(app.values,bot+'GroupBox35/txtNMobSelectSpeed','2000')
    engine.reset();engine.tick();assert engine.target_last.status=='retarget_armed'
    engine.tick();assert engine.target_last.status=='waiting'
    engine.tick();assert engine.target_last.candidate.target_id==11
    assert engine.target_controls.winfo_manager()=='grid'
    app.profiles.update(app.values,MODE_PATHS[1],True)
    app.lists[LIST_PATH]=[dict(caption='11',subitems=[],checked=True)]
    app.profiles.update(app.values,bot+'GroupBox35/txtNMobSelectSpeed','0')
    engine.reset();engine.tick();engine.tick()
    assert engine.target_last.candidate.target_id==11
    app.profiles.update(app.values,MODE_PATHS[0],True);engine.tick()
    assert engine.target_compiled.status=='helper_branch_mode' and engine.target_compiled.mode==1
    assert dict(engine.target_branch_last.writes)=={0x108:0x100000,0x10c:11,0x118:1}
    engine.ready.set(False);engine.tick()
    assert dict(engine.target_branch_last.writes)=={0x118:0,0x108:0,0x10c:0}
    app.profiles.update(app.values,MODE_PATHS[4],True);engine.tick()
    assert dict(engine.target_branch_last.writes)=={0x10c:11,0x108:0,0x118:1}
    assert not engine.target_branch_last.independently_verified
    app.profiles.update(app.values,MODE_PATHS[3],True);engine.tick()
    assert engine.target_compiled.status=='helper_branch_mode' and engine.target_compiled.mode==4
    assert engine.target_branch_last.status=='local_clear_plan' # Synthetic target lookup is0 while ready box is off.
    engine.ready.set(True);engine.tick()
    assert engine.target_branch_last.status=='local_write_plan'
    app.profiles.update(app.values,bot+'GroupBox35/txtNMobSelectDistance','2')
    engine.inputs['hp'].set('1');engine.tick()
    assert engine.target_branch_last.status=='local_no_write' # Outside/alive keeps prior fields.
    engine.inputs['hp'].set('0');engine.tick()
    assert engine.target_branch_last.status=='local_clear_plan'
    engine.ready.set(True)
    app.profiles.update(app.values,MODE_PATHS[2],True)
    app.profiles.update(app.values,bot+'GroupBox35/txtNMobSelectDistance','50')
    engine.target_pool.set('Panel')
    app.panel.set_value(POOL_PATHS[0],True)
    engine.reset();engine.tick();engine.tick()
    assert engine.target_compiled.settings.raw_pool_selector==2 and engine.target_last.candidate.target_id==11
    app.panel.set_value(POOL_PATHS[1],True)
    assert not app.values[POOL_PATHS[0]] and not app.panel.variables[POOL_PATHS[0]].get()
    assert app.values[POOL_PATHS[1]] and app.panel.variables[POOL_PATHS[1]].get()
    engine.reset();engine.tick();engine.tick()
    assert engine.target_compiled.settings.raw_pool_selector==1 and engine.target_last.candidate.target_id==12
    app.panel.set_value(POOL_PATHS[1],False)
    engine.reset();engine.tick();engine.tick()
    assert engine.target_compiled.settings.raw_pool_selector==0 and engine.target_last.candidate.target_id==11
    # Kurian panel lists drive the23-row/3-row selectors and the nested cycle.
    engine.use_class_panel.set(True)
    app.profiles.update(app.values,bot+'rdUseNormalSkill',True)
    app.profiles.update(app.values,bot+'GroupBox35/txtNAtackDistance','50')
    def kurian_only(flag):
        for path,offsets in schema['kurian']['lists'].items():
            for index,offset in enumerate(offsets):app.lists[path][index]['checked']=offset==flag
    kurian_only(0x3a)
    engine.ready.set(True);engine.inputs['distance'].set('8');engine.inputs['mp'].set('500')
    engine.case.set('Kurian Saldırı');engine.reset();engine.tick()
    assert engine.kurian_attack_last.row.skill_number==0x23c and engine.kurian_attack_last.source_return==1
    engine.inputs['mp'].set('499');engine.tick();assert engine.kurian_attack_last.status=='no_eligible_skill'
    engine.inputs['mp'].set('500');engine.inputs['distance'].set('9');engine.tick()
    assert engine.kurian_attack_last.status=='out_of_range' # Internal8 even with panel range50.
    engine.case.set('Kurian Özel');kurian_only(0xda);engine.reset()
    engine.inputs['distance'].set('32');engine.inputs['mp'].set('1');engine.tick()
    assert engine.kurian_attack_last.row.skill_number==0x2ee
    assert engine.kurian_attack_last.local_writes[-1]==('00561f7e',1)
    engine.inputs['distance'].set('33');engine.tick();assert engine.kurian_attack_last.status=='out_of_range'
    engine.case.set('Kurian Döngü');kurian_only(0x3a)
    for path,value in zip(COMBO_PANEL_INPUTS,(False,False,False,True)):app.profiles.update(app.values,path,value)
    engine.inputs['distance'].set('8');engine.inputs['mp'].set('500');engine.inputs['item_id'].set('99')
    engine.reset();engine.tick(1000)
    assert engine.kurian_cycle_last.selector.row.skill_number==0x23c and engine.kurian_cycle_state.phase==1
    engine.tick(49);assert engine.kurian_cycle_state.phase==1
    engine.tick(1);assert engine.kurian_cycle_state.phase==2
    assert engine.kurian_cycle_last.cycle.calls[-1]==('00465ef8',(99,1))
    engine.tick(199);assert engine.kurian_cycle_state.phase==2
    engine.tick(1);assert engine.kurian_cycle_state.phase==3
    assert engine.kurian_cycle_last.cycle.calls[-1]==('00465ef8',(99,0))
    app.profiles.update(app.values,COMBO_PANEL_INPUTS[1],True)
    engine.inputs['distance'].set('0');engine.tick(1)
    assert engine.kurian_cycle_state.phase==4 and engine.kurian_cycle_last.cycle.calls[-1]==('00465f30',(2,))
    engine.tick(20);assert engine.kurian_cycle_state.phase==5
    engine.tick(20);assert engine.kurian_cycle_state.phase==6
    engine.tick(609);assert engine.kurian_cycle_state.phase==0 #900ms from source start1000.
    from loot_configuration import GENERAL as LOOT_GENERAL,MODE_PATHS as LOOT_MODES
    app.profiles.update(app.values,LOOT_GENERAL+'chAutoLoot',True)
    app.profiles.update(app.values,LOOT_MODES[0],True)
    app.profiles.update(app.values,LOOT_GENERAL+'chLootBeforeWait',True)
    app.profiles.update(app.values,LOOT_GENERAL+'txtLootBeforeWait','1000')
    engine.case.set('Loot');engine.inputs['item_id'].set('900000000');engine.ready.set(True)
    engine.reset();engine.tick(1000);assert engine.loot_last.intents==()
    engine.tick(1);assert len(engine.loot_last.intents)==1
    app.profiles.update(app.values,LOOT_MODES[1],True)
    engine.inputs['item_id'].set('123');engine.reset();engine.tick(1001)
    assert engine.loot_last.intents==()
    engine.inputs['item_id'].set('900000000');engine.reset();engine.tick(1001)
    assert len(engine.loot_last.intents)==1 and engine.loot_last.intents[0].slot==0
    app.profiles.update(app.values,LOOT_MODES[2],True);engine.inputs['item_id'].set('123')
    engine.loot_source_fixture.set(False);engine.reset();engine.tick(1001)
    assert engine.loot_last.status=='needs_item_classifier' and engine.loot_last.intents==()
    assert engine.loot_pending is not None and engine.loot_last.records[0].item_attempt_ms==1001
    engine.tick(999);assert engine.loot_last.records[0].item_attempt_ms==1001 # Frozen incomplete invocation.
    app.profiles.update(app.values,LOOT_GENERAL+'chAutoLoot',False);engine.reset();engine.tick()
    assert engine.loot_last.status=='blocked'
    from loot_configuration import FILTER as LOOT_FILTER
    from loot_name_cache import LOOT_LIST_PATH
    for row in app.lists[LOOT_LIST_PATH]:
        if row['caption']=='Fork':row['subitems'][0]='EVET'
    app.profiles.update(app.values,LOOT_FILTER+'chLootNpcPrice',True)
    app.profiles.update(app.values,LOOT_FILTER+'txtLootNpcPrice','10.000')
    for name in ('chLootUpgrade','chLootCountable','chLootUnique'):app.profiles.update(app.values,LOOT_FILTER+name,False)
    engine.case.set('Loot Filtre');engine.inputs['item_id'].set('123');engine.loot_name.set('Fork')
    engine.inputs['quantity'].set('2');engine.inputs['threshold'].set('7');engine.inputs['price'].set('9999')
    engine.ready.set(True);engine.reset();engine.tick()
    assert engine.loot_classifier_last.attempt_slots==() and engine.loot_list_state.discarded==1
    engine.inputs['price'].set('10000');engine.tick()
    assert engine.loot_classifier_last.attempt_slots==() # Already-classified mask is reused.
    engine.reset();engine.tick();assert engine.loot_classifier_last.attempt_slots==(0,7)
    assert engine.loot_name_plan.ansi_bytes==b'Fork' and engine.loot_name_plan.read_count==255
    engine.ready.set(False);engine.reset();engine.tick();assert engine.loot_classifier_last.attempt_slots==()
    app.profiles.update(app.values,LOOT_FILTER+'chLootNpcPrice',False)
    app.profiles.update(app.values,LOOT_FILTER+'chLootUpgrade',True)
    app.profiles.update(app.values,LOOT_FILTER+'txtLootUpgrade','7')
    engine.ready.set(True);engine.inputs['price'].set('0');engine.reset();engine.tick()
    assert engine.loot_classifier_last.attempt_slots==(0,7)
    engine.loot_name.set('fork');engine.reset();engine.tick()
    assert engine.loot_classifier_last.status=='needs_observation' # No match preserves unknown old BYTE.
    engine.loot_name.set('Fork');engine.tick();assert engine.loot_classifier_last.attempt_slots==(0,7)
    for row in app.lists[LOOT_LIST_PATH]:
        if row['caption']=='Fork':row['subitems'][0]='HAYIR'
    engine.reset();engine.tick();assert engine.loot_classifier_last.attempt_slots==()
    assert engine.loot_cache_state.values[0]==0 and engine.loot_cache_state.values[7]==0
    for row in app.lists[LOOT_LIST_PATH]:
        if row['caption']=='Fork':row['subitems'][0]='EVET'
    engine.tick();assert engine.loot_classifier_last.attempt_slots==() # Classified record preserves old mask.
    engine.reset();engine.tick();assert engine.loot_classifier_last.attempt_slots==(0,7)
    app.lists[LOOT_LIST_PATH].append({'caption':'İtem','checked':False,'subitems':['EVET','HAYIR','HAYIR','HAYIR','0']})
    engine.loot_name.set('İtem')
    for page,data in (('1254',b'\xddtem'),('65001',b'\xc4\xb0tem')):
        engine.loot_codepage.set(page);engine.reset();engine.tick()
        assert engine.loot_name_plan.ansi_bytes==data
        assert engine.loot_name_conversion.compare_unicode=='İtem'
        assert engine.loot_classifier_last.attempt_slots==(0,7)
        assert not engine.loot_name_conversion.independently_verified
    engine.loot_codepage.set('1254');engine.loot_name.set('Fork')
    # Same composed producer can complete the actual Loot lifecycle path.
    app.profiles.update(app.values,LOOT_GENERAL+'chAutoLoot',True)
    app.profiles.update(app.values,LOOT_GENERAL+'chLootBeforeWait',False)
    engine.case.set('Loot');engine.inputs['item_id'].set('123');engine.loot_source_fixture.set(False)
    engine.inputs['quantity'].set('2');engine.inputs['threshold'].set('7');engine.inputs['price'].set('0')
    engine.reset();engine.tick(1000);assert not engine.loot_pipeline_last.complete
    assert engine.loot_last.records[0].item_attempt_ms==1000
    engine.tick(1000);assert engine.loot_last.records[0].item_attempt_ms==1000
    engine.loot_source_fixture.set(True);engine.tick(1)
    assert engine.loot_pipeline_last.complete and engine.loot_pending is None
    assert engine.loot_records[0].item_attempt_ms==1000 # Original callback sample, not wall-clock2001.
    assert engine.loot_records[0].list_state.classified==1
    assert len(engine.loot_last.intents)==1 and not engine.loot_records[0].slot_done[0]
    assert engine.loot_packet_last.complete
    assert engine.loot_packet_last.plans[0].payload==bytes.fromhex('26443322117b0000000000')
    engine.loot_source_fixture.set(False);engine.tick(1000)
    assert engine.loot_pipeline_last.complete and len(engine.loot_last.intents)==1
    assert engine.loot_pipeline_last.classification.cache is None # Cached record needs no new producer.
    # UI's monotonic demonstration counter supplies a masked source DWORD.
    from operation_engine import LootRecord
    app.profiles.update(app.values,LOOT_MODES[0],True)
    engine.reset();engine.initialized=True;engine.now_ms=0xfffffc18
    engine.loot_records=(LootRecord('wrap',0xfffffc18,item_ids=(123,0,0,0,0,0,0,0),
        item_phase=True,item_attempt_ms=0xfffffc18),)
    engine.ready.set(True);engine.tick(1000)
    assert engine.loot_pipeline_last.complete and len(engine.loot_last.intents)==1
    assert engine.loot_records[0].item_attempt_ms==0
    assert engine.loot_packet_last.status=='needs_bundle_id' # No guessed ID for custom record.
    engine.case.set('Loot');engine.reset();engine.ready.set(False);engine.tick(1000)
    assert engine.loot_packet_last.plans[0].payload==bytes.fromhex('2444332211')
    app.values.clear();app.values.update(saved_values);app.lists.clear();app.lists.update(saved_lists);app.panel.render()
    from supply_configuration import TRIGGERS as SUPPLY_TRIGGERS
    from control_guards import ROOT as CONTROL_ROOT
    control_values_before=dict(app.values)
    for name in ('chNPControl','chCoinControl','chLevelKontrol'):app.profiles.update(app.values,CONTROL_ROOT+name,True)
    app.profiles.update(app.values,CONTROL_ROOT+'txtCoinControlValue','100')
    app.profiles.update(app.values,CONTROL_ROOT+'txtLevelKontrol','54')
    engine.case.set('Kontrol');engine.use_class_panel.set(True)
    engine.control_guard_data.set(False);engine.control_guard_stop_return.set(False);engine.control_guard_town_return.set(False)
    engine.inputs['item_id'].set('0');engine.inputs['price'].set('100');engine.inputs['hp'].set('54')
    engine.reset();engine.tick()
    assert engine.control_guard_controls.winfo_manager()=='grid'
    assert engine.control_guard_last.missing=='00462718 DWORD return'
    engine.control_guard_data.set(True);engine.tick()
    assert engine.control_guard_last.missing=='0040ae0c normal return'
    engine.control_guard_stop_return.set(True);engine.tick()
    assert engine.control_guard_last.missing=='00465678 normal return'
    engine.control_guard_town_return.set(True);engine.tick()
    assert engine.control_guard_last.status=='np_zero_stop_town'
    assert [call[0] for call in engine.control_guard_last.calls]==['00462718','0040ae0c','00465678']
    engine.inputs['item_id'].set('1');engine.tick()
    assert engine.control_guard_last.status=='coins_at_or_below_stop_town'
    engine.inputs['price'].set('101');engine.tick()
    assert engine.control_guard_last.status=='level_equal_stop_town'
    engine.inputs['hp'].set('55');engine.tick()
    assert engine.control_guard_last.status=='entry_guards_passed'
    assert engine.control_guard_last.next_address==0x459071
    assert not engine.control_guard_last.source_return_planned
    assert not engine.control_guard_last.native_execution_verified
    app.profiles.update(app.values,CONTROL_ROOT+'txtCoinControlValue','-1');engine.inputs['price'].set(str(0xffffffff));engine.tick()
    assert engine.control_guard_last.status=='entry_guards_passed'
    app.profiles.update(app.values,CONTROL_ROOT+'txtCoinControlValue',str(1<<32));engine.tick()
    assert engine.control_guard_last.status=='coins_at_or_below_stop_town'
    for name in ('chNPControl','chCoinControl','chLevelKontrol'):app.profiles.update(app.values,CONTROL_ROOT+name,False)
    engine.control_guard_data.set(False);engine.control_guard_stop_return.set(False);engine.control_guard_town_return.set(False);engine.tick()
    assert engine.control_guard_last.complete and engine.control_guard_last.calls==()
    engine.control_follow_enabled.set(True)
    for name in ('chGameCloseClock','chPartyCountBotStop','chPartyCountAlarm','chPartyNotPriestBotStop','chPartyNotPriestAlarm'):
        app.profiles.update(app.values,CONTROL_ROOT+name,False)
    engine.control_follow_mode.set('Bilinmiyor');engine.tick()
    assert engine.control_continuation_last.missing=='global00561f58'
    engine.control_follow_mode.set('2');engine.tick()
    assert engine.control_chain_last.complete and engine.control_chain_last.next_address==0x459519
    engine.control_follow_mode.set('0')
    app.profiles.update(app.values,CONTROL_ROOT+'chPartyCountAlarm',True)
    app.profiles.update(app.values,CONTROL_ROOT+'txtPartyControlCount','5')
    engine.control_follow_counts.set('4');engine.tick()
    assert engine.control_continuation_last.missing=='00404260 normal return'
    engine.control_follow_alarm_return.set(True);engine.tick()
    assert engine.control_continuation_last.status=='party_count_below'
    assert not engine.control_continuation_last.native_execution_verified
    engine.control_follow_counts.set('5');engine.tick()
    assert engine.control_chain_last.complete and engine.control_chain_last.next_address==0x4592a7
    app.profiles.update(app.values,CONTROL_ROOT+'chPartyCountAlarm',False)
    app.profiles.update(app.values,CONTROL_ROOT+'chPartyNotPriestAlarm',True)
    engine.control_follow_counts.set('3,3');engine.control_follow_matches.set('{}');engine.tick()
    assert engine.control_continuation_last.missing=='00505d20 member1'
    engine.control_follow_matches.set('{"1":false}');engine.tick()
    assert engine.control_continuation_last.missing=='004645e4 count sample2'
    engine.control_follow_counts.set('3,3,3');engine.control_follow_matches.set('{"1":false,"2":true}');engine.tick()
    assert engine.control_chain_last.complete and engine.control_chain_last.next_address==0x4592a7
    engine.control_follow_counts.set('3,0');engine.control_follow_matches.set('{}');engine.tick()
    assert engine.control_continuation_last.status=='party_priest_not_found'
    app.profiles.update(app.values,CONTROL_ROOT+'chGameCloseClock',True)
    app.profiles.update(app.values,CONTROL_ROOT+'txtGameCloseHour','15')
    app.profiles.update(app.values,CONTROL_ROOT+'txtGameCloseMinute','0')
    engine.control_follow_hour.set('15');engine.control_follow_minute.set('0');engine.control_follow_handle.set('');engine.tick()
    assert engine.control_continuation_last.missing=='GetCurrentProcess handle'
    engine.control_follow_handle.set('1');engine.control_follow_mode.set('Bilinmiyor');engine.tick()
    assert engine.control_chain_last.complete and engine.control_continuation_last.termination_call_planned
    assert not engine.control_continuation_last.source_return_planned
    assert not engine.control_continuation_last.native_execution_verified
    assert engine.control_continuation_last.calls[-1]==('0050755e',(1,0))
    engine.control_follow_hour.set('14');engine.control_follow_minute.set('');engine.control_follow_handle.set('')
    engine.control_follow_mode.set('2');engine.tick()
    assert engine.control_chain_last.complete and engine.control_chain_last.next_address==0x459519
    # Earlier source return excludes continuation parsing and its unrelated invalid CSV.
    app.profiles.update(app.values,CONTROL_ROOT+'chNPControl',True)
    engine.control_guard_data.set(True);engine.inputs['item_id'].set('0')
    engine.control_guard_stop_return.set(True);engine.control_guard_town_return.set(True)
    engine.control_follow_counts.set('invalid');engine.tick()
    assert engine.control_chain_last.complete and engine.control_chain_last.continuation is None
    assert engine.control_guard_last.status=='np_zero_stop_town'
    engine.control_follow_enabled.set(False);engine.control_follow_counts.set('');engine.control_follow_matches.set('{}')
    engine.control_follow_hour.set('');engine.control_follow_mode.set('Bilinmiyor');engine.control_follow_alarm_return.set(False)
    engine.control_frame_enabled.set(True);engine.control_frame_json.set('invalid JSON');engine.tick()
    assert engine.control_frame_last.complete and engine.control_frame_last.entry.source_return_planned
    assert engine.control_frame_last.party_help is None # Earlier NP return excludes observation JSON parsing.
    for name in ('chNPControl','chCoinControl','chLevelKontrol','chGameCloseClock','chPartyCountBotStop',
                 'chPartyCountAlarm','chPartyNotPriestBotStop','chPartyNotPriestAlarm'):
        app.profiles.update(app.values,CONTROL_ROOT+name,False)
    from control_alarms import ROOT as CONTROL_ALARM_ROOT
    for name in ('chNoLootedItemAlarm','chDevilItemAlarm'):app.profiles.update(app.values,CONTROL_ALARM_ROOT+name,False)
    from party_help import ROOT as PARTY_HELP_ROOT
    for name in ('chHelpChatBuff','chHelpChatAC','chHelpChatSW','chHelpChatCure'):
        app.profiles.update(app.values,PARTY_HELP_ROOT+name,False)
    import json
    engine.control_follow_mode.set('0');engine.control_frame_json.set('{}');engine.reset();engine.tick()
    assert not engine.control_frame_last.complete and engine.control_frame_last.missing=='004645e4 DWORD count'
    engine.control_frame_json.set(json.dumps({'party_help':{'party_count':1}}));engine.tick()
    assert engine.control_frame_last.complete and engine.control_frame_last.source_return_planned
    assert dict(engine.control_frame_state.party_help.timers)=={}
    app.profiles.update(app.values,CONTROL_ALARM_ROOT+'chNoLootedItemAlarm',True)
    sample={'initial_state':{'timers':{'0x553cb4':0},'last_activity_qword':1},
        'party_help':{'party_count':2,'outer_tick':5000,'final_tick':5001},'alarms':{'now_tick':600001}}
    engine.control_frame_json.set(json.dumps(sample));engine.reset();engine.tick()
    assert engine.control_frame_last.status=='needs_alarm_observation'
    assert engine.control_frame_state.party_help.timers[0x553cb4]==0
    assert engine.control_frame_last.prospective_state.party_help.timers[0x553cb4]==5001
    sample['alarms']['alarm_returns']={'no_loot':True};engine.control_frame_json.set(json.dumps(sample));engine.tick()
    assert engine.control_frame_last.complete and engine.control_frame_state.party_help.timers[0x553cb4]==5001
    sample['initial_state']['timers']['0x553cb4']=99999 # A later input edit does not reseed accepted state.
    sample['party_help']['outer_tick']=5002;sample['alarms']['now_tick']=600002
    engine.control_frame_json.set(json.dumps(sample));engine.tick()
    assert engine.control_frame_last.party_help.status=='outer_timer_wait'
    assert engine.control_frame_state.party_help.timers[0x553cb4]==5001
    assert engine.control_frame_last.alarms.alarm_requests==('no_loot',)
    app.profiles.update(app.values,CONTROL_ALARM_ROOT+'chNoLootedItemAlarm',False)
    app.profiles.update(app.values,PARTY_HELP_ROOT+'chHelpChatBuff',True)
    sample={'initial_state':{'timers':{'0x553cb4':0,'0x553cbc':0}},'party_help':{'party_count':2,'outer_tick':10000,
        'feature_ticks':{'0x103':10000},'predicate_returns':{'0x103':1},'request_returns':{'0x103':True},
        'post_request_ticks':{'0x103':10001},'final_tick':10002}}
    engine.control_frame_json.set(json.dumps(sample));engine.reset();engine.tick()
    assert engine.control_frame_last.missing=='observed AnsiString field+108'
    sample['observed_ansi_hex']={PARTY_HELP_ROOT+'txtHelpChatBuff':'2b2b2b'}
    engine.control_frame_json.set(json.dumps(sample));engine.tick()
    assert engine.control_frame_last.complete and engine.control_frame_last.party_help.requests==((0x103,b'+++'),)
    assert engine.control_frame_state.party_help.timers[0x553cbc]==10001
    assert not engine.control_frame_last.party_help.messages_sent
    app.profiles.update(app.values,PARTY_HELP_ROOT+'chHelpChatBuff',False)
    app.profiles.update(app.values,CONTROL_ALARM_ROOT+'chDevilItemAlarm',True)
    sample={'party_help':{'party_count':1}}
    engine.control_frame_json.set(json.dumps(sample));engine.tick()
    assert engine.control_frame_last.missing=='fresh name slot14 comparison0'
    sample['alarms']={'name_samples':[[14,0,b'Teeth of Devil'.hex()]],'alarm_returns':{'devil_item':True}}
    engine.control_frame_json.set(json.dumps(sample));engine.tick()
    assert engine.control_frame_last.complete and engine.control_frame_last.alarms.matching_sample==(14,0)
    assert not engine.control_frame_last.native_execution_verified
    app.profiles.update(app.values,CONTROL_ALARM_ROOT+'chDevilItemAlarm',False)
    app.profiles.update(app.values,CONTROL_ALARM_ROOT+'chNoLootedItemAlarm',True)
    engine.control_follow_mode.set('2');engine.control_frame_json.set('{}');engine.reset();engine.tick()
    assert engine.control_frame_last.complete and engine.control_frame_last.party_help is None
    assert engine.control_frame_state.loot_activity.last_activity_qword is None
    engine.control_frame_enabled.set(False);engine.control_frame_json.set('{}')
    engine.use_class_panel.set(False);engine.tick();assert engine.control_guard_last is None
    engine.case.set('Upgrade');engine.reset();assert engine.control_guard_controls.winfo_manager()==''
    app.values.clear();app.values.update(control_values_before)
    engine.case.set('Tedarik');engine.use_class_panel.set(True);engine.ready.set(True)
    engine.inputs['hp'].set('95');engine.inputs['hp_max'].set('100')
    app.profiles.update(app.values,SUPPLY_TRIGGERS+'chTedarikWeight',True)
    app.profiles.update(app.values,SUPPLY_TRIGGERS+'txtTedarikWeightLimit','95')
    engine.reset();engine.tick(1)
    assert engine.supply_weight_last.due and engine.supply_weight_last.action=='supply_route'
    assert engine.supply_compiled.status=='needs_combo_text'
    engine.inputs['hp'].set('94');engine.tick(1);assert not engine.supply_weight_last.due
    app.profiles.update(app.values,SUPPLY_TRIGGERS+'txtTedarikWeightLimit','94')
    app.profiles.update(app.values,SUPPLY_TRIGGERS+'chSupplyTownAlarm',True)
    engine.tick(1);assert engine.supply_weight_last.action=='town_alarm'
    engine.ready.set(False);engine.tick(1);assert engine.supply_weight_last.status=='weight_branch_not_reached'
    from supply_stock import BUY_LIST_PATH
    app.lists[BUY_LIST_PATH]=[{'caption':'Caption is ignored','checked':False,'subitems':['200','9']}]
    engine.inputs['item_id'].set('391010000');engine.inputs['quantity'].set('10')
    engine.tick(1);assert engine.supply_stock_last.due
    assert engine.supply_stock_last.row_index==9 and engine.supply_stock_last.matched_slot==14
    engine.inputs['quantity'].set('11');engine.tick(1);assert not engine.supply_stock_last.due
    app.lists[BUY_LIST_PATH][0]['subitems'][0]='1000'
    engine.tick(1);assert not engine.supply_stock_last.due # Desired total is not stock threshold.
    engine.inputs['item_id'].set('123');engine.tick(1)
    assert engine.supply_stock_last.status=='stock_item_absent'
    app.lists[BUY_LIST_PATH][0]['subitems'][1]='22';engine.tick(1)
    assert not engine.supply_list_last.complete and engine.supply_stock_last.due is None
    from mining_configuration import ORE as MINING_ORE,REPAIR as MINING_REPAIR
    from mining_engine import MiningExecutionState
    engine.case.set('Maden');engine.use_class_panel.set(True)
    app.profiles.update(app.values,MINING_ORE+'chUseSpeedSkill',False)
    engine.mining_scheduler_fixture.set(False);engine.mining_dead.set(False)
    engine.reset();engine.tick(1)
    assert not engine.mining_frame_last.complete and engine.mining_frame_last.missing==('scheduler.active_initial',)
    assert engine.mining_pipeline_last is None and engine.mining_state.phase==0
    engine.mining_scheduler_fixture.set(True)
    app.profiles.update(app.values,MINING_ORE+'chGoCrashWait',True)
    app.profiles.update(app.values,MINING_ORE+'txtGoCrashWait','1')
    engine.reset();engine.tick(60000);assert engine.mining_state.phase==0
    engine.tick(1);assert engine.mining_state.phase==1 and engine.mining.config.crash_wait_minutes==1
    app.profiles.update(app.values,MINING_ORE+'chPitmanFollow',True)
    engine.mining_state=MiningExecutionState(phase=1,route_active=True)
    engine.tick(1);assert engine.mining_last.required_observations==('helper_479988_result',)
    app.profiles.update(app.values,MINING_ORE+'chMiningVipStorage',False)
    app.profiles.update(app.values,MINING_REPAIR+'chMiningMHBotStop',True)
    engine.mining_state=MiningExecutionState(phase=5,route_active=True)
    engine.tick(1);assert engine.mining_state.phase==6
    app.profiles.update(app.values,MINING_ORE+'chMiningVipStorage',True)
    engine.mining_state=MiningExecutionState(phase=5,route_active=True)
    engine.tick(1);assert engine.mining_state.auxiliary_flag
    assert engine.mining_last.intents[0].name=='begin_storage_operation_5'
    app.profiles.update(app.values,MINING_ORE+'txtOreCrashSpeed','2')
    app.profiles.update(app.values,MINING_ORE+'chOreCrashWS',True)
    engine.tick(1);assert engine.mining_ore_settings.interval_seconds==2 and engine.mining_ore_settings.ws_enabled
    engine.mining_fixture.set(True);engine.mining_ws_zero.set(True);engine.mining_request_zero.set(True)
    engine.mining_name_fixture.set(True);engine.mining_name_kind.set('Ore')
    engine.ready.set(True);engine.inputs['quantity'].set('1');engine.inputs['distance'].set('1')
    engine.mining_state=MiningExecutionState(phase=2,route_active=True,item_index=14)
    engine.tick(1)
    assert engine.mining_pipeline_last.complete and engine.mining_state.item_index==15
    assert engine.mining_ore_state.item_index==15 and engine.mining_ore_state.ws_counter==1
    assert engine.mining_pipeline_last.ore.intents[0].value==1
    assert not engine.mining_pipeline_last.server_acknowledged
    assert engine.mining_local_complete and engine.mining_name_request_last.name.ansi_bytes==b'Mysterious Ore'
    assert len(engine.mining_request_queue.records)==2
    assert [(r.delay_dword,len(r.payload)) for r in engine.mining_request_queue.records]==[(300,8),(600,19)]
    assert engine.mining_request_queue.records[1].payload[1]==0
    assert engine.inputs['quantity'].get()=='1' # Never invent an ore inventory update from a request.
    engine.tick(1000);assert engine.mining_state.item_index==15 #2-second cadence.
    engine.mining_request_zero.set(False);engine.tick(1000)
    assert engine.mining_state.item_index==15 and engine.mining_ore_state.ws_counter==2
    engine.mining_fixture.set(False)
    engine.tick(1);assert not engine.mining_pipeline_last.complete and engine.mining_state.item_index==15
    assert len(engine.mining_request_queue.records)==2
    engine.mining_fixture.set(True);engine.mining_name_fixture.set(False);engine.mining_request_zero.set(True)
    engine.tick(2000)
    assert engine.mining_pipeline_last.complete and not engine.mining_local_complete
    assert engine.mining_name_request_last.request.status=='needs_fresh_ansi_name'
    assert engine.mining_state.item_index==15 and len(engine.mining_request_queue.records)==2
    engine.mining_name_fixture.set(True);engine.mining_name_kind.set('Gold');engine.tick(1)
    assert engine.mining_local_complete and engine.mining_state.item_index==16
    assert len(engine.mining_request_queue.records)==4 and engine.mining_request_queue.records[-1].payload[1]==1
    engine.mining_name_kind.set('Boş yuva');engine.tick(2000)
    assert engine.mining_local_complete and engine.mining_state.item_index==17
    assert engine.mining_name_request_last.name.status=='empty_slot'
    assert engine.mining_name_request_last.request.status=='source_early_return'
    assert len(engine.mining_request_queue.records)==4 and engine.inputs['quantity'].get()=='1'
    app.profiles.update(app.values,MINING_ORE+'chMiningAutoRespawn',True)
    app.profiles.update(app.values,MINING_ORE+'txtMiningAutoRespawn','1')
    engine.mining_dead.set(True);engine.reset();engine.tick(4000)
    assert engine.mining_frame_last.scheduler.status=='respawn_wait'
    assert engine.mining_pipeline_last is None and engine.mining_state.phase==0
    engine.tick(1)
    assert engine.mining_frame_last.scheduler.status=='respawn_planned'
    assert engine.mining_frame_last.scheduler.calls==( ('004c8d48',(0x561ef8,)), )
    assert engine.mining_scheduler_times[0x553df0]==4001
    assert engine.mining_pipeline_last is None and engine.mining_request_queue.records==()
    engine.tick(999);assert engine.mining_frame_last.scheduler.status=='respawn_retry_wait'
    assert engine.mining_scheduler_times[0x553df0]==4001
    engine.tick(1);assert engine.mining_scheduler_times[0x553df0]==5001
    engine.mining_dead.set(False);engine.tick(1)
    assert engine.mining_frame_last.complete and engine.mining_pipeline_last is not None
    assert engine.mining_state.phase==0 # Existing one-minute route wait still applies.
    engine.mining_scheduler_fixture.set(False);engine.tick(1)
    assert not engine.mining_frame_last.complete and engine.mining_pipeline_last is None
    assert engine.mining_scheduler_times[0x553df0]==5001
    engine.mining_scheduler_fixture.set(True);engine.mining_speed_fixture.set(False)
    app.profiles.update(app.values,MINING_ORE+'chUseSpeedSkill',True)
    engine.reset();engine.tick(2000)
    assert not engine.mining_frame_last.complete and engine.mining_frame_last.missing==('speed',)
    assert engine.mining_pipeline_last is None
    app.profiles.update(app.values,MINING_ORE+'rdUseSprint',True)
    app.profiles.update(app.values,MINING_ORE+'rdUseSwift',False)
    app.profiles.update(app.values,MINING_ORE+'rdUseLightFeet',False)
    engine.mining_speed_fixture.set(True);engine.mining_speed_family.set('Rogue');engine.tick(1)
    assert engine.mining_frame_last.speed.status=='speed_planned' and engine.mining_local_complete
    assert engine.mining_frame_last.speed.calls==(('004655e8',(2,1)),)
    assert engine.mining_speed_values[0x553de8]==2001
    app.profiles.update(app.values,MINING_ORE+'rdUseSprint',False)
    app.profiles.update(app.values,MINING_ORE+'rdUseSwift',True)
    engine.mining_speed_success.set(False);engine.tick(2000)
    assert engine.mining_frame_last.speed.status=='swift_cast_failed'
    assert engine.mining_speed_values[0x553de8]==2001 and engine.mining_speed_values[0x561f7e]==0
    engine.mining_speed_success.set(True);engine.tick(1)
    assert engine.mining_frame_last.speed.status=='swift_planned'
    assert engine.mining_speed_values[0x561f7e]==1 and engine.mining_speed_values[0x561f80]==2000
    assert engine.mining_speed_values[0x553de8]==4002
    assert engine.mining_pipeline_last.ore is None and engine.mining_state.phase==0
    engine.tick(3000);assert engine.mining_frame_last.speed.status=='locked'
    assert engine.mining_speed_values[0x561f7e]==1 # No invented automatic unlock/ACK.
    app.profiles.update(app.values,MINING_ORE+'chUseSpeedSkill',False)
    engine.mining_callback_fixture.set(True);engine.tick(1)
    assert engine.mining_callback_last.complete and engine.mining_callback_last.unlock.status=='lock_cleared'
    assert engine.mining_speed_values[0x561f7e]==0
    assert engine.mining_speed_values[0x561f80]==2000 and engine.mining_speed_values[0x561f84]==4002
    assert not engine.mining_callback_last.native_execution_verified and not engine.mining_callback_last.server_acknowledged
    # Bound control uses profile settings and independent post-helper samples.
    mining_control_saved=dict(app.values)
    for name in ('chNPControl','chCoinControl','chLevelKontrol','chGameCloseClock','chPartyCountBotStop',
                 'chPartyCountAlarm','chPartyNotPriestBotStop','chPartyNotPriestAlarm'):
        app.profiles.update(app.values,CONTROL_ROOT+name,False)
    for name in ('chNoLootedItemAlarm','chDevilItemAlarm'):
        app.profiles.update(app.values,CONTROL_ALARM_ROOT+name,False)
    for name in ('chHelpChatBuff','chHelpChatAC','chHelpChatSW','chHelpChatCure'):
        app.profiles.update(app.values,PARTY_HELP_ROOT+name,False)
    engine.mining_control_enabled.set(True);engine.mining_callback_fixture.set(False)
    engine.mining_control_guard_json.set('{}');engine.control_follow_mode.set('Bilinmiyor')
    engine.control_frame_json.set('invalid JSON')
    engine.mining_control_timer_lock.set('invalid future JSON');engine.mining_control_post_lock.set('invalid future JSON')
    engine.reset();engine.tick(2000)
    assert not engine.mining_local_complete and engine.mining_callback_last.control.status=='needs_control_observation'
    assert engine.mining_frame_last is None # Unknown mode excludes later JSON/lock parsing.
    engine.control_follow_mode.set('2');engine.control_frame_json.set('{}');engine.mining_control_timer_lock.set('')
    engine.tick(1)
    assert engine.mining_callback_last.control.status=='needs_timer_lock_observation'
    assert engine.mining_speed_values[0x561f7e]==0
    fresh_locked=json.dumps({'byte':1,'duration_ms':9000,'started_ms':0})
    fresh_clear=json.dumps({'byte':0,'duration_ms':2000,'started_ms':0})
    engine.mining_control_timer_lock.set(fresh_locked);engine.tick(1)
    assert engine.mining_callback_last.status=='needs_post_timer_segment'
    assert engine.mining_callback_last.prospective_state.lock.byte==1
    assert engine.mining_speed_values[0x561f7e]==0 # No commit across later gaps.
    engine.mining_control_segment_return.set(True);engine.mining_control_post_lock.set('');engine.tick(1)
    assert engine.mining_callback_last.status=='needs_post_timer_lock'
    engine.mining_control_post_lock.set(fresh_clear);engine.mining_control_post_mode.set('');engine.tick(1)
    assert engine.mining_callback_last.status=='needs_callback_mode'
    engine.mining_control_post_mode.set('2');engine.tick(1)
    assert engine.mining_callback_last.complete and engine.mining_callback_last.control.control_return_assumed_from_local_plan
    assert engine.mining_callback_last.unlock.status=='wait_lock_duration'
    assert engine.mining_speed_values[0x561f7e]==0 # Later independent sample overrides earlier locked BYTE.
    assert engine.mining_speed_values[0x561f80]==2000
    # Help timestamp is prospective until the complete callback is accepted.
    engine.control_follow_mode.set('0');engine.mining_control_segment_return.set(False)
    control_sample={'initial_state':{'timers':{'0x553cb4':0}},
        'party_help':{'party_count':2,'outer_tick':5000,'final_tick':5001}}
    engine.control_frame_json.set(json.dumps(control_sample));engine.mining_control_timer_lock.set(fresh_clear)
    engine.reset();engine.tick(2000)
    assert engine.mining_callback_last.status=='needs_post_timer_segment'
    assert engine.mining_control_state.party_help.timers[0x553cb4]==0
    assert engine.mining_callback_last.prospective_state.control.party_help.timers[0x553cb4]==5001
    engine.mining_control_segment_return.set(True);engine.tick(1)
    assert engine.mining_local_complete and engine.mining_control_state.party_help.timers[0x553cb4]==5001
    control_sample['initial_state']['timers']['0x553cb4']=99999
    control_sample['party_help']['outer_tick']=6000
    engine.control_frame_json.set(json.dumps(control_sample));engine.tick(1)
    assert engine.mining_callback_last.control.control.party_help.status=='outer_timer_wait'
    assert engine.mining_control_state.party_help.timers[0x553cb4]==5001
    # A process-termination plan cannot reach lock or later observations.
    app.profiles.update(app.values,CONTROL_ROOT+'chGameCloseClock',True)
    app.profiles.update(app.values,CONTROL_ROOT+'txtGameCloseHour','13')
    app.profiles.update(app.values,CONTROL_ROOT+'txtGameCloseMinute','42')
    engine.control_follow_hour.set('13');engine.control_follow_minute.set('42');engine.control_follow_handle.set('1')
    engine.control_frame_json.set('invalid JSON');engine.mining_control_timer_lock.set('invalid JSON')
    engine.tick(1)
    assert engine.mining_callback_last.control.status=='control_return_unproven'
    assert engine.mining_frame_last is None and not engine.mining_local_complete
    assert not engine.mining_callback_last.native_execution_verified
    # The recovered interlude itself replaces the external completion marker.
    app.profiles.update(app.values,CONTROL_ROOT+'chGameCloseClock',False)
    engine.control_follow_hour.set('');engine.control_follow_minute.set('');engine.control_follow_handle.set('')
    engine.control_follow_mode.set('Bilinmiyor');engine.control_frame_json.set('{}')
    engine.mining_interlude_enabled.set(True);engine.mining_control_enabled.set(False)
    engine.mining_interlude_json.set('invalid future JSON')
    engine.mining_control_timer_lock.set(fresh_clear);engine.mining_control_post_lock.set('invalid future JSON')
    engine.mining_control_segment_return.set(True) # Legacy marker cannot bypass the source model.
    engine.reset();engine.tick(2000)
    assert engine.mining_callback_last.control.status=='needs_control_observation'
    assert engine.mining_callback_last.interlude is None
    engine.control_follow_mode.set('2');engine.mining_interlude_json.set('{}');engine.tick(1)
    assert engine.mining_callback_last.status=='needs_interlude_observation'
    assert engine.mining_callback_last.interlude.missing=='interlude GetTickCount DWORD'
    assert engine.mining_frame_last is None
    interlude_sample={'initial_state':{'interval_dword':1000,'last_attempt_qword':0},
        'observation':{'tick':3000,'session_stamp_qword':0,'predicate_al':1,'flag_after_predicate':1}}
    engine.mining_interlude_json.set(json.dumps(interlude_sample));engine.reset();engine.tick(2000)
    assert engine.mining_callback_last.interlude.missing=='final random helper DWORD return'
    assert engine.mining_interlude_state.last_attempt_qword==0
    assert engine.mining_callback_last.prospective_state.interlude.last_attempt_qword==3000
    interlude_sample['observation']['final_random_return']=70000
    engine.mining_interlude_json.set(json.dumps(interlude_sample));engine.mining_control_post_lock.set('');engine.tick(1)
    assert engine.mining_callback_last.status=='needs_post_timer_lock'
    assert engine.mining_interlude_state.interval_dword==1000
    assert engine.mining_callback_last.prospective_state.interlude.interval_dword==70000
    engine.mining_control_post_lock.set(fresh_clear);engine.mining_control_post_mode.set('2');engine.tick(1)
    assert engine.mining_local_complete and engine.mining_callback_last.interlude.segment_fallthrough_planned
    assert engine.mining_interlude_state.interval_dword==70000 and engine.mining_interlude_state.last_attempt_qword==3000
    assert not engine.mining_callback_last.interlude.native_execution_verified
    interlude_sample['initial_state']={'interval_dword':0,'last_attempt_qword':99999}
    interlude_sample['observation']={'tick':3001,'session_stamp_qword':0}
    engine.mining_interlude_json.set(json.dumps(interlude_sample));engine.tick(1)
    assert engine.mining_callback_last.interlude.status=='session_interval_wait'
    assert engine.mining_interlude_state.interval_dword==70000 # Seed edits ignored until reset.
    engine.reset();engine.tick(2000)
    assert engine.mining_callback_last.status=='needs_interlude_observation'
    assert engine.mining_callback_last.interlude.missing=='initial random helper DWORD return'
    # Bound predicate has its own clock and still needs the fresh caller flag.
    interlude_sample={'initial_state':{'interval_dword':1000,'last_attempt_qword':0},
        'observation':{'tick':3000,'session_stamp_qword':0,'final_random_return':70000,
                       'predicate_inputs':{'mode_byte':0}}}
    engine.mining_interlude_json.set(json.dumps(interlude_sample));engine.reset();engine.tick(2000)
    assert engine.mining_callback_last.interlude.missing=='predicate GetTickCount DWORD'
    assert engine.mining_interlude_state.last_attempt_qword==0
    interlude_sample['observation']['predicate_inputs'].update(tick=300000,stamp_qword=0)
    engine.mining_interlude_json.set(json.dumps(interlude_sample));engine.tick(1)
    assert engine.mining_callback_last.interlude.missing=='fresh00555e23 BYTE'
    assert engine.mining_callback_last.interlude.predicate_plan.al==1
    assert (0x555e23,1,8) in engine.mining_callback_last.interlude.writes
    assert engine.mining_interlude_state.last_attempt_qword==0
    interlude_sample['observation']['flag_after_predicate']=1
    engine.mining_interlude_json.set(json.dumps(interlude_sample));engine.tick(1)
    assert engine.mining_local_complete
    assert engine.mining_callback_last.interlude.predicate_plan.complete
    assert engine.mining_interlude_state.last_attempt_qword==3000
    # All three random helpers use independent observed CRT snapshots.
    random_sample={'initial_state':{'interval_dword':0,'last_attempt_qword':0},
        'observation':{'tick':100000,'session_stamp_qword':0,
            'initial_random_inputs':{'tick':11,'srand_returned':True,'rand_eax':0},
            'session_stamp_after_random':0,'last_attempt_after_random':0,
            'predicate_inputs':dict(mode_byte=1,enabled_byte=1,minutes_dword=0,
                field_555dd8=0xffffffff,field_555de4=0xffffffff,
                field_555ddc=0xffffffff,field_555de0=0xffffffff,
                random_inputs={'tick':22,'srand_returned':True,'rand_eax':2},
                tick=300000,stamp_qword=0),
            'flag_after_predicate':1,
            'final_random_inputs':{'tick':33,'srand_returned':False,'rand_eax':7}}}
    engine.mining_interlude_json.set(json.dumps(random_sample));engine.reset();engine.tick(2000)
    assert engine.mining_callback_last.interlude.missing=='random helper srand normal return'
    assert engine.mining_interlude_state.interval_dword==0
    assert engine.mining_callback_last.prospective_state.interlude.last_attempt_qword==100000
    assert engine.mining_callback_last.interlude.predicate_plan.random_plan.result_dword==5
    random_sample['observation']['final_random_inputs']['srand_returned']=True
    engine.mining_interlude_json.set(json.dumps(random_sample));engine.tick(1)
    assert engine.mining_local_complete
    assert engine.mining_interlude_state.interval_dword==60007
    assert engine.mining_interlude_state.last_attempt_qword==100000
    assert engine.mining_callback_last.interlude.initial_random_plan.result_dword==60000
    assert engine.mining_callback_last.interlude.final_random_plan.result_dword==60007
    # Disk CRT replay is explicit and keeps its stable-context contract separate.
    random_sample['observation']['final_random_inputs']={'tick':0,'srand_returned':True,'disk_crt_replay':True}
    engine.mining_interlude_json.set(json.dumps(random_sample));engine.reset();engine.tick(2000)
    assert engine.mining_callback_last.interlude.missing=='disk CRT replay stable thread context'
    assert engine.mining_interlude_state.interval_dword==0
    random_sample['observation']['final_random_inputs']['same_thread_context']=True
    engine.mining_interlude_json.set(json.dumps(random_sample));engine.tick(1)
    assert engine.mining_local_complete and engine.mining_interlude_state.interval_dword==60346
    assert engine.mining_callback_last.interlude.final_random_plan.rand_source=='local_disk_crt_replay'
    assert not engine.mining_callback_last.interlude.final_random_plan.crt_replay.loaded_game_runtime_verified
    engine.mining_interlude_enabled.set(False);engine.mining_interlude_json.set('{}')
    engine.mining_control_enabled.set(False);engine.mining_callback_fixture.set(True)
    engine.control_frame_json.set('{}');engine.control_follow_mode.set('2')
    engine.control_follow_hour.set('');engine.control_follow_minute.set('');engine.control_follow_handle.set('')
    app.values.clear();app.values.update(mining_control_saved)
    app.profiles.update(app.values,MINING_ORE+'chUseSpeedSkill',True)
    app.profiles.update(app.values,MINING_ORE+'rdUseSwift',False)
    app.profiles.update(app.values,MINING_ORE+'rdUseLightFeet',True)
    engine.reset();engine.tick(2000)
    assert engine.mining_frame_last.speed.calls==(('004655e8',(725,1)),)
    engine.mining_speed_family.set('Warrior');engine.tick(2000)
    assert not engine.mining_frame_last.complete
    assert engine.mining_frame_last.missing==('speed.stack_uninitialized_1',)
    app.profiles.update(app.values,MINING_ORE+'chUseSpeedSkill',False)
    for path in (MINING_REPAIR+'chMiningChangeMattock',MINING_REPAIR+'chMiningUseMagicHammer',
        MINING_REPAIR+'chMiningMHBotStop',MINING_ORE+'chMiningVipStorage',MINING_ORE+'chOreFullAlarm',
        MINING_ORE+'chGoCrash',MINING_REPAIR+'chMiningGoRPR'):
        app.profiles.update(app.values,path,False)
    engine.mining_callback_fixture.set(False);engine.mining_maintenance_active.set(True)
    engine.mining_maintenance_fixture.set(False);engine.mining_post_route.set(True)
    engine.mining_post_lock.set('Bilinmiyor');engine.reset();engine.tick(2000)
    assert not engine.mining_local_complete and engine.mining_frame_last.missing==('maintenance',)
    engine.mining_maintenance_fixture.set(True);engine.mining_maintenance_case.set('Boş');engine.tick(1)
    assert not engine.mining_local_complete and engine.mining_frame_last.missing==('post_maintenance_lock_byte',)
    engine.mining_post_lock.set('0');engine.tick(1)
    assert engine.mining_local_complete and engine.mining_frame_last.maintenance.status=='tail_gate_blocked'
    app.profiles.update(app.values,MINING_REPAIR+'chMiningChangeMattock',True)
    engine.mining_maintenance_case.set('Kazma');engine.tick(1)
    assert engine.mining_frame_last.maintenance.calls==(('004651bc',(14,)),)
    assert engine.inputs['quantity'].get()=='1' # No equipment/inventory ACK invented.
    app.profiles.update(app.values,MINING_REPAIR+'chMiningChangeMattock',False)
    app.profiles.update(app.values,MINING_REPAIR+'chMiningUseMagicHammer',True)
    engine.mining_maintenance_case.set('Hammer');engine.reset();engine.tick(4000)
    assert engine.mining_local_complete and engine.mining_maintenance_values[0x553de0]==4000
    assert engine.mining_frame_last.maintenance.calls==(('00465640',(0x77ada,1)),)
    engine.tick(1);assert engine.mining_frame_last.maintenance.calls==()
    app.profiles.update(app.values,MINING_REPAIR+'chMiningMHBotStop',True)
    engine.mining_maintenance_case.set('Hammer yok');engine.mining_post_route.set(False);engine.tick(1)
    assert engine.mining_frame_last.maintenance.status=='missing_hammer_stop_planned'
    assert [a for a,_ in engine.mining_frame_last.maintenance.calls]==['00464d10','0040ae0c']
    assert engine.mining_pipeline_last is None
    engine.mining_post_route.set(True)
    app.profiles.update(app.values,MINING_REPAIR+'chMiningUseMagicHammer',False)
    app.profiles.update(app.values,MINING_ORE+'chMiningVipStorage',True)
    engine.mining_maintenance_case.set('Dolu');engine.reset();engine.tick(1000)
    assert engine.mining_frame_last.maintenance.status=='tail_gate_blocked'
    engine.tick(1)
    assert engine.mining_frame_last.maintenance.status=='vip_operation4_planned'
    assert engine.mining_maintenance_values[0x5690bc]==4 and engine.mining_maintenance_values[0x5690b8]==1
    engine.tick(1);assert engine.mining_frame_last.maintenance.status=='storage_active'
    app.profiles.update(app.values,MINING_ORE+'chMiningVipStorage',False)
    app.profiles.update(app.values,MINING_ORE+'chOreFullAlarm',True)
    app.profiles.update(app.values,MINING_ORE+'chGoCrash',True)
    engine.mining_post_route.set(False);engine.reset();engine.tick(2000)
    assert engine.mining_frame_last.maintenance.status=='full_alarm_stop_planned'
    assert [a for a,_ in engine.mining_frame_last.maintenance.calls]==['00464d10','00404260','0040ae0c']
    app.profiles.update(app.values,MINING_ORE+'chOreFullAlarm',False);engine.tick(1)
    assert not engine.mining_local_complete and engine.mining_frame_last.missing==('maintenance_effect.start',)
    engine.mining_effect_fixture.set(True);engine.mining_post_route.set(True)
    app.profiles.update(app.values,MINING_ORE+'chMattockExtract',True)
    engine.tick(1)
    assert engine.mining_frame_last.maintenance.status=='ore_crash_start_planned'
    assert engine.mining_frame_last.maintenance.calls==( ('004779dc',('self',)), )
    assert engine.mining_frame_last.maintenance_effect.start.calls==( ('0046526c',(6,0)), )
    assert engine.mining_state.phase==0 and engine.mining_state.item_index==14
    assert engine.mining_state.started_ms==engine.now_ms
    assert not engine.mining_maintenance_active.get() # known source write global561f6c=0
    app.profiles.update(app.values,MINING_ORE+'chGoCrash',False);engine.mining_post_route.set(True)
    app.profiles.update(app.values,MINING_REPAIR+'chMiningGoRPR',True)
    engine.mining_maintenance_active.set(True)
    from mining_configuration import START_MODES
    for index,path in enumerate(START_MODES):app.profiles.update(app.values,path,index==0)
    for case_name,route_name,count in (('Onarım EMC','EMCMiningRoute2',15),
        ('Onarım Luferson','LFCMiningRoute2',23),('Onarım Moradon','MoradonMiningRoute2',31)):
        engine.mining_maintenance_case.set(case_name);engine.reset();engine.tick(2000)
        assert engine.mining_local_complete
        assert engine.mining_repair_route_last.name==route_name and len(engine.mining_repair_route_last.steps)==count
        assert not engine.mining_repair_route_last.native_pointer_blob_reconstructed
        assert not engine.mining_frame_last.native_execution_verified
    engine.mining_maintenance_active.set(False);engine.mining_effect_fixture.set(False)
    engine.mining_state=MiningExecutionState(phase=7,route_active=True,item_index=14);engine.tick(1)
    assert not engine.mining_local_complete and engine.mining_frame_last.missing==('route_effect.returning',)
    assert engine.mining_state.route_active
    app.profiles.update(app.values,MINING_ORE+'chMiningAutoSell',True)
    app.profiles.update(app.values,MINING_ORE+'chMiningAutoBank',False)
    engine.mining_effect_fixture.set(True);engine.mining_effect_candidates.set('Satış');engine.mining_effect_region.set('Moradon')
    engine.tick(1)
    assert engine.mining_local_complete and not engine.mining_state.route_active
    assert engine.mining_frame_last.route_effect.returning.route.name=='MoradonMiningRoute2'
    assert engine.mining_frame_last.route_effect.sell.available and not engine.mining_frame_last.route_effect.bank.available
    assert not engine.mining_frame_last.route_effect.native_execution_verified
    engine.mining_effect_candidates.set('Yok');engine.mining_effect_region.set('EMC')
    engine.mining_state=MiningExecutionState(phase=7,route_active=True,item_index=14);engine.tick(1)
    assert not engine.mining_local_complete and engine.mining_state.route_active
    assert engine.mining_frame_last.route_effect.returning.route.name=='EMCMiningRoute4'
    assert engine.mining_frame_last.route_effect.returning.route.status=='incomplete_source_route'
    engine.mining_maintenance_active.set(True)
    engine.mining_maintenance_case.set('Boş');engine.mining_post_route.set(False);engine.tick(1)
    assert engine.mining_local_complete and engine.mining_pipeline_last is None
    assert not engine.mining_state.route_active
    app.values.clear();app.values.update(saved_values);app.lists.clear();app.lists.update(saved_lists);app.panel.render()
    engine.case.set('Upgrade');engine.reset();assert engine.target_controls.winfo_manager()==''
    npc_saved_values=dict(app.values)
    app.profiles.update(app.values,MINING_REPAIR+'chDontRPRWithSell',True)
    app.profiles.update(app.values,MINING_ORE+'chMiningVipStorage',False)
    route.npc_profile_fixture.set(True);route.toggle_npc_profile()
    route.npc_runtime_mode.set('Bilinmiyor');route.npc_kind.set('Sundries')
    route.npc_helper_fixture.set(False);route.npc_worker_fixture.set(False)
    route.special_ready.set(True);route.steps=[RouteStep('NPC',parameter1='Sundries')];route.refresh();route.start()
    route.tick();route.tick();route.tick()
    assert not route.npc_profile_last.complete and route.npc_profile_last.missing=='global00561f58'
    assert route.npc_frame.phase==3
    route.npc_runtime_mode.set('2');route.tick()
    assert route.npc_frame.phase==4 and route.npc_profile_last.result.calls==()
    route.npc_complete.set(True) # The legacy whole-helper checkbox cannot bypass inner replay.
    route.tick();assert route.npc_frame.phase==4 and route.runner.processing
    route.tick();assert not route.npc_profile_last.complete and route.npc_profile_last.missing=='004fe384 return'
    route.npc_helper_fixture.set(True)
    for _ in range(10):route.tick()
    assert route.runner.reason=='Tamamlandı'
    assert not route.npc_profile_last.native_execution_verified and not route.npc_profile_last.server_acknowledged
    route.npc_runtime_mode.set('1');route.npc_helper_fixture.set(False);route.start()
    route.tick();route.tick();route.tick()
    assert route.npc_frame.phase==3 and route.npc_frame.fields[0x63c]==1
    route.tick();assert route.npc_profile_last.missing=='004edf34 return'
    app.profiles.update(app.values,MINING_ORE+'chMiningVipStorage',True)
    route.npc_runtime_mode.set('2');route.npc_helper_fixture.set(True);route.start()
    for _ in range(6):route.tick()
    assert route.npc_frame.phase==5 and route.npc_frame.globals[0x5690b8]==1
    assert route.npc_frame.globals[0x5690bc]==2
    route.tick();assert route.npc_frame.phase==5 # No invented worker completion.
    route.npc_worker_fixture.set(True);route.tick();assert route.npc_frame.phase==6
    for _ in range(6):route.tick()
    assert route.runner.reason=='Tamamlandı'
    app.profiles.update(app.values,MINING_ORE+'chMiningVipStorage',False)
    route.npc_worker_fixture.set(False);route.npc_entry.set('Aşama1')
    route.npc_lookup_fixture.set(False);route.npc_name_fixture.set(False);route.start()
    route.tick();route.tick();route.tick()
    assert route.npc_frame.phase==1 and route.npc_profile_last.missing=='00465960:undries return'
    route.npc_lookup_fixture.set(True);route.tick()
    assert route.npc_frame.phase==2 and route.npc_frame.fields[0x604]==17
    assert 0x610 not in route.npc_frame.texts
    route.tick();assert route.npc_frame.phase==2 and route.npc_profile_last.missing=='00464a10 return'
    route.npc_name_fixture.set(True);route.tick()
    assert route.npc_frame.phase==3 and route.npc_frame.texts[0x610]=='Sundries'
    assert route.npc_profile_last.result.text_request.byte_count==255
    assert not route.npc_profile_last.result.text_request.indirect
    for _ in range(12):route.tick()
    assert route.runner.reason=='Tamamlandı'
    # Long-name entry follows the separate indirect source branch, not the inline255 copy.
    route.npc_kind.set('Royal National Enchanter');route.start()
    for _ in range(4):route.tick()
    assert route.npc_frame.phase==3 and route.npc_frame.texts[0x610]=='Royal National Enchanter'
    assert route.npc_profile_last.result.text_request.indirect
    assert route.npc_profile_last.result.text_request.address==0x200000
    assert route.npc_profile_last.result.text_request.byte_count==len(b'Royal National Enchanter')
    route.npc_kind.set('Sundries');route.npc_runtime_mode.set('1')
    route.npc_nested_fixture.set(True);route.start()
    child_calls=[];child_phases=[];child_packets=[];purchase_counts=[]
    for _ in range(80):
        route.tick(1000)
        if route.npc_profile_last is not None:
            assert route.npc_profile_last.complete
            child_calls.extend(route.npc_profile_last.result.calls)
            child_phases.append(route.npc_frame.phase)
            child_packets.extend(route.npc_profile_last.result.queue_payloads)
            if 0x68c in route.npc_frame.fields:purchase_counts.append(route.npc_frame.fields[0x68c])
        if route.runner.reason=='Tamamlandı':break
    assert route.runner.reason=='Tamamlandı' and route.npc_frame.phase==11
    assert '004edc40' in child_calls # Counted typed empty repair inventory, not constant42.
    assert child_calls.count('004637d8')==28 # Every bag slot14..41 is visited by the sale model.
    assert '004f0108' in child_calls and '00462630' in child_calls # Buy retarget/wait/disabled row.
    # Results record post-call phases: the first successful phase1 lookup returns phase2.
    assert set((2,3,4,5,6,7,8,11)).issubset(set(child_phases))
    assert set(purchase_counts)=={1} and not child_packets
    assert not route.npc_profile_last.native_execution_verified and not route.npc_profile_last.server_acknowledged
    route.npc_repair_case.set('Hasarlı ekipman1');route.start()
    for _ in range(6):route.tick(1000)
    assert route.npc_frame.phase==3 and route.npc_frame.fields[0x644]==1
    assert route.npc_frame.fields[0x640]==0
    route.tick(1000)
    assert route.npc_profile_last.missing=='repair:global00561fb0'
    assert 0x561fb0 not in route.npc_frame.globals
    route.npc_reply_hex.set('3b00');route.apply_npc_reply()
    assert route.npc_reply_last.plan.handled and route.npc_frame.globals[0x561fb0]==0
    route.tick(1000);assert route.npc_frame.fields[0x640]==1 and route.npc_frame.fields[0x644]==0
    route.tick(1000)
    assert route.npc_profile_last.result.queue_payloads[0].hex()=='3b010111000000c8000000'
    assert route.npc_frame.globals[0x561fb0]==0xffffffff
    route.tick(1000)
    assert route.npc_frame.fields[0x640]==1 and route.npc_frame.fields[0x644]==1
    assert not route.npc_profile_last.result.queue_payloads
    pending_repair_frame=route.npc_frame
    route.npc_reply_hex.set('not hex');route.apply_npc_reply()
    assert route.npc_frame is pending_repair_frame
    route.npc_reply_hex.set('3b01');route.apply_npc_reply()
    assert not route.npc_reply_last.plan.complete and route.npc_frame is pending_repair_frame
    route.npc_reply_hex.set('3b0178563412');route.apply_npc_reply()
    assert route.npc_reply_last.plan.missing=='00467f10 normal return'
    assert route.npc_frame is pending_repair_frame
    route.npc_reply_refresh.set(True);route.apply_npc_reply()
    assert route.npc_reply_last.plan.handled and route.npc_frame.globals[0x561fb0]==1
    assert not route.npc_reply_last.plan.native_execution_verified
    assert not route.npc_reply_last.plan.server_acknowledged
    # The branch has no pending-request correlation: a later status0 replaces status1.
    route.npc_reply_refresh.set(False);route.npc_reply_hex.set('3b00');route.apply_npc_reply()
    assert route.npc_frame.globals[0x561fb0]==0
    route.tick(1000)
    assert route.npc_frame.fields[0x640]==4 and route.npc_frame.fields[0x644]==0
    for _ in range(90):
        route.tick(1000)
        if route.runner.reason=='Tamamlandı':break
    assert route.runner.reason=='Tamamlandı'
    completed_repair_frame=route.npc_frame;route.apply_npc_reply()
    assert route.npc_frame is completed_repair_frame and 'etkin yerel NPC' in route.status.get()
    route.npc_repair_case.set('Boş');route.npc_reply_hex.set('')
    route.npc_nested_fixture.set(False)
    route.npc_entry.set('Aşama3');route.npc_lookup_fixture.set(False);route.npc_name_fixture.set(False)
    route.npc_profile_fixture.set(False);route.toggle_npc_profile();route.npc_complete.set(False);route.stop()
    app.values.clear();app.values.update(npc_saved_values)
    # Connection rendering uses explicit fake observations, never a game process.
    from concurrent.futures import Future
    from game_provider import Observation
    connection = app.connection_page
    connection.mode.set('native')
    connection.publisher_pid.set('invalid')
    connection.check()
    assert connection.pending is None
    assert 'ayarları geçersiz' in connection.result.get()
    fields = dict(hp=250, hp_max=500, mp=100, mp_max=300)
    for status in ('fixture_candidate', 'candidate_unverified', 'stale'):
        completed = Future()
        completed.set_result(Observation(status, pid=123, fields=fields if status != 'stale' else {}, error='Expired sample'))
        connection.pending = completed
        connection.pending_mode = 'native'
        # Changing controls during an in-flight result must not change its source label.
        connection.mode.set('external')
        connection.poll()
        text = connection.result.get()
        if status == 'fixture_candidate':assert 'sentetik veri' in text
        elif status == 'candidate_unverified':assert 'doğrulanmayı bekliyor' in text
        else:assert 'kabul edilmedi (stale)' in text and 'Expired sample' in text
        assert connection.pending is None and connection.pending_mode is None
    # A computed digest alone cannot promote an unknown build to a match.
    for matched in (False,True):
        completed=Future()
        completed.set_result(Observation('unavailable',pid=123,image_sha256='f'*64,
            error='Test read unavailable',disk_identity_verified=matched))
        connection.pending=completed;connection.pending_mode='external';connection.poll()
        if matched:
            assert 'Kayıtlı oyun dosyası eşleşti' in connection.result.get()
            assert 'Oyun dosyası eşleşti' in connection.status.get()
        else:
            assert 'dosya sürümü doğrulanmadı' in connection.result.get()
            assert 'eşleşti' not in connection.status.get()
        assert 'canlı veri alınamadı' in connection.result.get().lower()
    print('UI smoke passed: 1037 controls across 11 forms, 18 main tabs, detail rendering, search, HP/MP and routes')
    print('Connection UI passed: invalid binding, fixture, unverified candidate and stale result; simulated observations only')
    print('Rogue derived UI effect passed: panel option, normal radio, sibling exclusion and latched choice')
    print('Support panel bridge passed: Priest skill/threshold, Minor speed, Kurian boundary and Mage text/threshold')
    print('Attack parameter panel bridge passed: Provoke waits/flag and Rogue volley distance boundary')
    print('Alternate Rogue bow passed: panel combo radius boundary and explicit selection-only fixture')
    print('Rogue chain passed: head routing, nested selector, 5ms steps, reselection and cycle interval; synthetic observations')
    print('Callback lock passed: persisted lock state, 599/600ms boundary and selector retains old duration/start; synthetic observations')
    print('Combo panel passed: W-only, S-only and both switches reach their source branches; no runtime bit fixture when panel enabled')
    print('Kurian panel passed: normal/special list selection, MP/range limits, nested cycle and R/S flags; synthetic game observations')
    print('Loot panel passed: enable/mode/strict wait, coins first slot and explicit unresolved LIST classifier; synthetic bundle')
    print('Loot classifier passed: panel NPC9999/10000, upgrade7, post-cache0/1 and persisted classification mask; synthetic metadata')
    print('Loot name cache passed: panel TOPLA EVET/HAYIR, exact Unicode names, no-match unknown and classified-mask persistence')
    print('Name byte/codec/cache chain passed: captured inline255 ANSI, explicit Windows1254/65001 and Turkish name; local fixtures only')
    print('Loot lifecycle chain passed: timer-before-helper, frozen missing-producer pass, explicit fixture completion and cached retry without ACK')
    print('Loot DWORD clock passed: UI source timestamp wraps to0 at unsigned1000ms boundary')
    print('Loot serializers passed: explicit synthetic bundle DWORD, open5/take11 bytes and missing custom ID')
    print('Supply panel passed: weight95/94 boundary, panel threshold/alarm and explicit branch gate; route Text unresolved')
    print('Control panel passed: NP/coin/level profile flags, unknown query/stop/Town return gates, inclusive signed64 coin threshold and exact level equality, disabled short-circuit and bounded continuation; no game effects')
    print('Control continuation UI passed: explicit mode/clock/handle/count sequence/Priest comparisons, strict count boundary, missing alarm return, earlier-guard short-circuit and process-termination plan only; no process or game action')
    print('Control full-frame UI passed: JSON observations remain unverified, parent-return short-circuit, unknown help/ANSI/name gates, persisted timers and alarm-prefix freeze/commit, no-loot repeat and mode2 skip; no messaging or game action')
    print('Supply BuyList/stock passed: source Arrow index9, unchecked caption ignored,10/11, desired independence and unresolved index')
    print('Source .R INI import passed: own Windows profile API file -> route UI -> runner; zero count/unsupported rows preserve prior route')
    print('Panel route start passed: source flags/lists -> cyclic/manual fallback -> own INI; independent counters and execution error stop intent')
    print('Other8 route kinds passed:7 direct ANSI stand-ins, Mine third counter and separate check/load directories; no trigger detection or native movement')
    print('Mining scalar panel passed: strict minute60000/60001, Pitman override6035, VIP604c distinct from hammer-stop6039; ore settings projected only')
    print('Mining nested ore passed: panel cadence/WS, fresh slot/name/request, gold/ore/empty, queue delays, missing-name holds and no invented inventory ACK')
    print('Mining scheduler composition passed: explicit outer fixture, exclusive respawn4000/4001 and retry999/1000, persisted stamps, alive route resume; no native action')
    print('Mining speed composition passed: panel Sprint/Swift/LightFeet, missing fixture, failed/success Swift, same-frame persistent lock and Warrior stack gap; no native skill')
    print('Mining callback bridge passed: explicit mode2/prefix/intermediate fixtures, timer clear before mining, preserved duration/start; no real callback or queue effects')
    print('Mining control callback UI passed: bound local control, lazy reached observations, independent timer/post-segment lock and mode, timestamp prefix freeze/commit, seed-once and termination-return gate; no native/game effects')
    print('Interlude callback UI passed: full local control/unlock/interlude/mining binding, source clock and random gaps, ignored legacy completion, lazy parsing, prefix freeze/commit and reset-only seed; no native or pointer effects')
    print('Mining maintenance bridge passed: independent data/post-lock/route gates, mattock, Hammer cadence/missing stop, VIP1000/1001, alarm/crash priority, persisted state,15/23/31 repair rows; no game effects')
    print('Mining effect composition passed: protected start/return helpers, source phase/index/tick writes and extract slot6, candidate producers -> phase7 return, EMC4gap; no native effects or ACK')
    print('NPC profile route bridge passed: independent mode missing/2/1, source repair skip/start, legacy bypass disabled, typed inner steps and VIP wait/explicit worker fixture; no live NPC or ACK')
    print('NPC source entry passed: phase1 missing lookup -> typed candidate -> phase2 missing pointer -> ANSI inline255/indirect long name -> phase3; synthetic observations, no process reads')
    print('NPC child composition passed: typed empty repair inventory, all28 empty sale slots and one disabled buy row through waits/inner phases; no constant completion markers or native/server effects')
    print('Repair reply UI passed: damaged source item100/producer200 request, missing initial ACK and pending reply hold, malformed/truncated/success helper-return gates, status overwrite/slot advance, completed-task rejection; no native or live ACK')
    print('Active bot panel bridge passed: range selection, manual interval and source Mage cap')
    print('Family panel bridge passed: five head pairs, explicit runtime override, normal-only guard and separate states')
    print('Target panel bridge passed: auto radius/wait, checked name-ID list and manual/leader/AutoZ plans')
    print('Pool source-checkbox bridge passed:2/1/0 selector, sibling widget exclusion and synthetic A/B results')
    print('Upgrade panel bridge passed: milliseconds1500, anvil42, checked caption FIFO, unresolved combo Text, explicit synthetic gate and no game effects')
    print('Upgrade source clock passed: signed negative interval, explicit synthetic initial/post-helper stamps, no monotonic-clock substitution')
    print('Upgrade scroll scan passed: owned per-slot ANSI fixtures, last relative slot27, exhaustive missing scroll stops without consuming queue; no live inventory')
    print('Upgrade source start passed: initial scan gates row conversion/start, deferred invalid caption preserves prefix, explicit local clear/UI/append returns; no native startup')
    print('Upgrade execution passed: source start ->57byte serializer -> local queue, independent gate0/nonzero and three distinct fixture clocks; no drain or game send')
    print('Armor execution passed: source startup from owned NPC/coordinate observations, two independent enqueues, helper/caller cleanup/stamp gates,43 local attempts/86 records; no native search/send/ACK')
    print('Armor startup passed: separate combo reads0/1, stable panel6 -> source item, blank5 rejects before second read, NPC0/full startup errors and later fresh bag gate')
finally:
    if 'app' in globals():
        app.connection_page.close()
    root.destroy()
