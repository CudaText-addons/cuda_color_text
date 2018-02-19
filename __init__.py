from cudatext import *
import os
import shutil
import string
import unicodedata as ud
from .colorcode import *

ini = os.path.join(app_path(APP_DIR_EXE),'tools', 'settings', 'styles.ini')
ini0 = os.path.join(os.path.dirname(__file__), 'styles.sample.ini')

all_unicode = ''.join(chr(i) for i in range(65536))
unicode_letters = ''.join(c for c in all_unicode
                          if ud.category(c)=='Lu' or ud.category(c)=='Ll')

CHARS = string.ascii_letters + string.digits + '_' + unicode_letters

if app_api_version()<'1.0.214':
    msg_box(MSG_ERROR, 'Plugin needs newer CudaText')

if os.path.isfile(ini0) and not os.path.isfile(ini):
    shutil.copyfile(ini0, ini)

#-------options
ALL_WORDS      = ini_read(ini, 'op', 'all_words'      , '1')
WHOLE_WORDS    = ini_read(ini, 'op', 'whole_words'    , '0')
WORDS_ONLY     = ini_read(ini, 'op', 'words_only'     , '0')
CASE_SENSITIVE = ini_read(ini, 'op', 'case_sensitive' , '0')
#-----constants
COLOR_FONT = 0x000000
TAG_UNIQ   = 12345
#--------------

def is_word(s):
    for ch in s:
        if not ch in CHARS: return False
    return True

def get_word(x, y):
    if x==0: return

    x0 = x
    while (x0>0) and is_word(ed.get_text_substr(x0-1, y, x0, y)):
        x0-=1
    text1 = ed.get_text_substr(x0, y, x, y)

    x0 = x
    while is_word(ed.get_text_substr(x0, y, x0+1, y)):
        x0+=1
    text2 = ed.get_text_substr(x, y, x0, y)

    return text1 + text2

def _curent_word():
    s = ed.get_text_sel()
    nlen = len(s)
    if nlen <= 0:
        carets = ed.get_carets()
        if len(carets)!=1: return
        x0, y0, x1, y1 = carets[0]
        return get_word(x0, y0)
    else:
        return ed.get_text_sel()


def do_find_all(ed, text):
    if int(WORDS_ONLY)>0:
        if not is_word(text): return

    res = []
    for i in range(ed.get_line_count()):
        line = ed.get_text_line(i)
        if not line: continue

        if int(CASE_SENSITIVE)>0:
            line = line.upper()
            text = text.upper()

        n = 0
        while True:
            n = line.find(text, n)
            if n<0: break
            allow = True
            if int(WORDS_ONLY)>0:
                if n>0 and is_word(line[n-1]):
                    allow = False
                if allow:
                    n2 = n+len(text)
                    if n2<len(line) and is_word(line[n2]):
                        allow = False
            if allow:
                res += [(i, n)]
            n += len(text)
    return res

def set_sel_attribute(item, nlen, attribs):
    tag, color, bold, italic, strikeout, border, color_border = attribs

    b_l = b_r = b_d = b_u = 0
    if border:
        b_l = b_r = b_d = b_u = 1

    fcolor = COLOR_FONT
    if bold or italic or strikeout or border:
        fcolor = COLOR_NONE

    ed.attr(MARKERS_ADD, tag, item[1], item[0], nlen, fcolor, color, color_border, bold, italic, strikeout, b_l, b_r, b_d, b_u)

def set_text_attribute(attribs):
    word = _curent_word()

    if not word:
        word = get_text_sel()

    if not word: return

    if int(ALL_WORDS) > 0:
        items = do_find_all(ed, word)
        for item in items:
            set_sel_attribute(item, len(word), attribs)
    else:
        x0, y0, x1, y1 = carets[0]
        if x0 > x1:
            x0, x1 = x1, x0

        set_sel_attribute([x0, y0], len(word), attribs)

# attribs array:
#[tag=n, color=COLOR_NONE, bold=0, italic=0, strikeout=0, border=0, color_border=COLOR_NONE]

def do_color(n):
    ed.attr(MARKERS_DELETE_BY_TAG, TAG_UNIQ + n)

    color        = COLOR_NONE
    color_border = COLOR_NONE
    bold         = 0
    italic       = 0
    strikeout    = 0
    border       = 0

    st = ini_read(ini, 'colors', str(n), '')
    if st:
        color = HTMLColorToPILColor(st)

    st = ini_read(ini, 'border_colors', str(n), '')
    if st:
        color_border = HTMLColorToPILColor(st)

    st = ini_read(ini, 'styles', str(n), '')
    if st:
        if 'b' in st: bold      = 1 #attribs.extend([(ATTRIB_SET_BOLD,0)])
        if 'i' in st: italic    = 1 #attribs.extend([(ATTRIB_SET_ITALIC,0)])
        if 'u' in st: border    = 1 #attribs.extend([(ATTRIB_SET_UNDERLINE,0)])
        if 's' in st: strikeout = 1 #attribs.extend([(ATTRIB_SET_STRIKEOUT,0)])

    set_text_attribute([TAG_UNIQ + n, color, bold, italic, strikeout, border, color_border])

def clear_style(n):
    ed.attr(MARKERS_DELETE_BY_TAG, TAG_UNIQ + n)

class Command:
    def color1(self): do_color(1)
    def color2(self): do_color(2)
    def color3(self): do_color(3)
    def color4(self): do_color(4)
    def color5(self): do_color(5)
    def color6(self): do_color(6)

    def format_bold(self):
        set_text_attribute([TAG_UNIQ, COLOR_NONE, 1, 0, 0, 0, COLOR_NONE])
    def format_italic(self):
        set_text_attribute([TAG_UNIQ, COLOR_NONE, 0, 1, 0, 0, COLOR_NONE])
    def format_strikeout(self):
        set_text_attribute([TAG_UNIQ, COLOR_NONE, 0, 0, 1, 0, COLOR_NONE])

    def clear_all(self): ed.attr(MARKERS_DELETE_ALL, 0)

    def clear1(self): clear_style(1)
    def clear2(self): clear_style(2)
    def clear3(self): clear_style(3)
    def clear4(self): clear_style(4)
    def clear5(self): clear_style(5)
    def clear6(self): clear_style(6)

    def edit(self): file_open(ini)
