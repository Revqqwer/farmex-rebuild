"""Owned Upgrade Text reader and callback context, no native/game context."""
from dataclasses import dataclass
from upgrade_configuration import SCROLL_PATH,ANVIL_PATH,WAIT_PATH

PARAMETER_PATHS={'scroll':SCROLL_PATH,'anvil':ANVIL_PATH,'wait':WAIT_PATH}


@dataclass(frozen=True)
class UpgradeParameterContext:
    invocation:int
    generation:int
    trigger_path:str
    phase:str
    needed:object


def read_parameter_text(field,values,catalog,widgets,cache,variables=None):
    if field not in PARAMETER_PATHS:raise ValueError('Known Upgrade text field required')
    path=PARAMETER_PATHS[field];widget=widgets.get(path)
    # Tk variable traces run before the Entry display has refreshed. The
    # StringVar already contains the Text that triggered this callback.
    if field!='scroll' and variables is not None and path in variables:
        text=variables[path].get()
        if type(text) is not str:raise ValueError('Own edit variable Unicode Text required')
        return text
    if widget is not None and widget.winfo_exists():
        text=widget.get()
        if type(text) is not str:raise ValueError('Own widget Unicode Text required')
        if field=='scroll':cache[path]=(values[path],text)
        return text
    if field!='scroll':
        text=values[path]
        if type(text) is not str:raise ValueError('Own hidden edit Unicode Text required')
        return text
    index=values[path]
    if type(index) is not int:raise ValueError('Own combo ItemIndex required')
    known=cache.get(path)
    if known is not None and known[0]==index:return known[1]
    node=next(n for n in catalog if n['path']==path)
    choices=node['properties'].get('Items.Strings',[])
    if not 0<=index<len(choices):raise ValueError('Hidden combo Text not observed')
    return choices[index]


def remember_scroll_text(values,widgets,cache):
    widget=widgets.get(SCROLL_PATH)
    if widget is not None and widget.winfo_exists():
        text=widget.get()
        if type(text) is not str:raise ValueError('Own combo Unicode Text required')
        cache[SCROLL_PATH]=(values[SCROLL_PATH],text)


def restore_scroll_text(widget,values,cache):
    known=cache.get(SCROLL_PATH)
    if values[SCROLL_PATH]==-1 and known is not None and known[0]==-1:widget.set(known[1])
