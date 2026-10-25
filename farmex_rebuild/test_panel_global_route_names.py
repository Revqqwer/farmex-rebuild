import unittest
from global_route_choices import ROUTE_GLOBALS,compile_panel_route_name,plan_global_route_choice
from route_catalog import ROUTE_COMBO_PATHS
from supply_routes import SupplyRouteState
from name_codec import WindowsNameCodec

class PanelGlobalRouteNameTests(unittest.TestCase):
    def test_each_kind_projects_distinct_control_to_exact_global_and_choice(self):
        texts={ROUTE_COMBO_PATHS[k]:k+'.R' for k in ROUTE_GLOBALS}
        for kind,address in ROUTE_GLOBALS.items():
            with self.subTest(kind=kind):
                projected=compile_panel_route_name(kind,texts,WindowsNameCodec(1254))
                self.assertEqual(dict(projected),{address:(kind+'.R').encode('ascii')})
                kwargs=dict(mine_change_byte=0) if kind=='Mine' else {}
                choice=plan_global_route_choice(kind,projected,SupplyRouteState(0,0),**kwargs)
                self.assertTrue(choice.complete);self.assertEqual(choice.filename,(kind+'.R').encode('ascii'))
                self.assertFalse(choice.independently_verified)
    def test_only_reached_name_is_required_and_unknown_is_not_empty(self):
        name=ROUTE_COMBO_PATHS['Notice'];codec=WindowsNameCodec(1254)
        self.assertEqual(dict(compile_panel_route_name('Notice',{name:'',ROUTE_COMBO_PATHS['Mine']:None},codec)),{ROUTE_GLOBALS['Notice']:b''})
        for texts in ({},{name:None},{name:0}):
            with self.assertRaises(ValueError):compile_panel_route_name('Notice',texts,codec)
    def test_lossy_name_rejected_and_utf8_projection_is_explicit(self):
        texts={ROUTE_COMBO_PATHS['SMerchant']:'😀.R'}
        with self.assertRaises(ValueError):compile_panel_route_name('SMerchant',texts,WindowsNameCodec(1254))
        self.assertEqual(compile_panel_route_name('SMerchant',texts,WindowsNameCodec(65001))[ROUTE_GLOBALS['SMerchant']], '😀.R'.encode('utf-8'))
    def test_projection_does_not_mutate_inputs_and_requires_explicit_codec(self):
        texts={ROUTE_COMBO_PATHS['Relog']:'İsim.R'};before=dict(texts)
        output=compile_panel_route_name('Relog',texts,WindowsNameCodec(1254))
        self.assertEqual(texts,before)
        with self.assertRaises(TypeError):output[ROUTE_GLOBALS['Relog']]=b'x'
        with self.assertRaises(ValueError):compile_panel_route_name('Relog',texts,None)
        with self.assertRaises(ValueError):compile_panel_route_name('supply',texts,WindowsNameCodec(1254))

if __name__=='__main__':unittest.main()
