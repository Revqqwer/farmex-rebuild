"""Normal-value search Enter/Exit actions from 004b1724/004b1808.

SetText precedes SetColor. The UI adapter must preserve that order because
SetText can synchronously invoke OnChange with the previous color.
"""
from dataclasses import dataclass
from merchant_result_filter import raw

BLACK=0
GRAY_TEXT=0xff000011
PLACEHOLDER='Aranan item ismini yazınız...'


@dataclass(frozen=True)
class SearchFocusPlan:
    changed: bool
    text: str
    color: int
    rebuild_requested: bool=False
    native_execution_verified: bool=False


def plan_search_focus(text, color, phase, placeholder=PLACEHOLDER):
    if type(text) is not str or type(placeholder) is not str:
        raise ValueError('Explicit own decoded Unicode text required')
    raw(color,32,'font color')
    if phase not in ('enter','exit'):raise ValueError('Known focus phase required')
    target=placeholder if phase=='enter' else ''
    # Source Unicode equality works on UTF16 code units, including embedded NUL.
    same=text.encode('utf-16-le','surrogatepass')==target.encode('utf-16-le','surrogatepass')
    if not same:return SearchFocusPlan(False,text,color)
    return SearchFocusPlan(True,'' if phase=='enter' else placeholder,
        BLACK if phase=='enter' else GRAY_TEXT,phase=='exit')
