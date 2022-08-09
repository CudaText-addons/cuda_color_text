# coding=utf8
import os
import json
import string
from cudatext import *
from cudax_lib import html_color_to_int

ini = os.path.join(app_path(APP_DIR_SETTINGS), 'cuda_color_text.ini')
ini0 = os.path.join(os.path.dirname(__file__), 'styles.sample.ini')

HELPER_EXT = '.cuda-colortext'
NONWORD = ''' \t-+*=/\()[]{}<>"'.,:;~?!@#$%^&|`…'''

if os.path.isfile(ini0) and not os.path.isfile(ini):
    import shutil
    shutil.copyfile(ini0, ini)

opt_all_words = False
opt_whole_words = False
opt_case_sens = False
opt_show_on_map = False

def str_to_bool(s): return s=='1'
def bool_to_str(v): return '1' if v else '0'
def bool_to_int(v): return 1 if v else 0

def load_ops():
    global opt_all_words
    global opt_whole_words
    global opt_case_sens
    global opt_show_on_map

    opt_all_words    = str_to_bool(ini_read(ini, 'op', 'all_words'      , '0'))
    opt_whole_words  = str_to_bool(ini_read(ini, 'op', 'whole_words'    , '0'))
    opt_case_sens    = str_to_bool(ini_read(ini, 'op', 'case_sensitive' , '0'))
    opt_show_on_map  = str_to_bool(ini_read(ini, 'op', 'show_on_map'    , '0'))

#-----constants
TAG_UNIQ   = 4000 # must be unique for all ed.attr() plugins
TAG_MAX    = TAG_UNIQ + 10
#--------------

def is_word(s):

    if not s:
        return False
    for ch in s:
        if ch in NONWORD:
            return False
    return True

def get_word(ed, x, y):

    s = ed.get_text_line(y)
    if not s: return
    if x>=len(s): return

    x0 = x
    while (x0>0) and is_word(s[x0-1]):
        x0 -= 1

    x1 = x
    while (x1<len(s)) and is_word(s[x1]):
        x1 += 1

    return s[x0:x1]

def _curent_word(ed):

    if ed.get_sel_mode() != SEL_NORMAL: return
    s = ed.get_text_sel()
    if s: return s

    carets = ed.get_carets()
    if len(carets)!=1: return
    x0, y0, x1, y1 = carets[0]
    return get_word(ed, x0, y0)


def do_find_all(ed, text):

    res = []
    for i in range(ed.get_line_count()):
        line = ed.get_text_line(i)
        if not line: continue

        if not opt_case_sens:
            line = line.upper()
            text = text.upper()

        n = 0
        while True:
            n = line.find(text, n)
            if n<0: break
            allow = True
            if opt_whole_words:
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


def set_sel_attribute(ed, x0, y0, x1, y1, attr):

    tag = attr['tag']
    color_back = attr['c_back']
    color_font = attr['c_font']
    color_border = attr['c_border']
    styles = attr['styles']
    bold      = 'b' in styles
    italic    = 'i' in styles
    strikeout = 's' in styles
    underline = 'u' in styles
    border    = 'o' in styles

    b_l = b_r = b_d = b_u = 0
    if border:
        b_l = b_r = b_d = b_u = 1
    elif underline:
        b_d = 1

    def _put(x, y, nlen):
        ed.attr(MARKERS_ADD, tag,
            x, y,
            nlen,
            color_font,
            color_back,
            color_border,
            bool_to_int(bold),
            bool_to_int(italic),
            bool_to_int(strikeout),
            b_l, b_r, b_d, b_u,
            show_on_map = opt_show_on_map,
            map_only = (2 if opt_show_on_map else 0)
            )

    if y0==y1:
        _put(x0, y0, x1-x0)
    elif y0>=0:
        cnt = ed.get_line_count()
        ok = 0<=y0<cnt and 0<=y1<cnt
        if not ok:
            return
        # multi-line selection: make 3 steps: first line, middle line(s), last line
        s = ed.get_text_line(y0)
        nlen = len(s) if s else 0
        _put(x0, y0, nlen-x0)
        for y in range(y0+1, y1):
            s = ed.get_text_line(y)
            nlen = len(s) if s else 0
            _put(0, y, nlen)
        _put(0, y1, x1)


def set_text_attribute(ed, attr):

    load_ops()

    carets = ed.get_carets()
    if not carets:
        return
    if len(carets)>1:
        return msg_status('Color Text: multi-carets are not supported')
    x0, y0, x1, y1 = carets[0]
    is_sel = y1>=0

    if not is_sel and opt_all_words:
        word = _curent_word(ed)
        if not word:
            return msg_status('Color Text: need a selection or caret on a word')

        items = do_find_all(ed, word)
        for item in items:
            x0 = item[1]
            y0 = item[0]
            x1 = x0 + len(word)
            y1 = y0
            set_sel_attribute(ed, x0, y0, x1, y1, attr)
        msg_status('Color Text: applied attribute to %d fragment(s)'%len(items))
    else:
        if not is_sel:
            return msg_status('Color Text: need a selection or option all_words=1')
        #sort pairs
        if (y0, x0)>(y1, x1):
            x0, y0, x1, y1 = x1, y1, x0, y0
        set_sel_attribute(ed, x0, y0, x1, y1, attr)
        msg_status('Color Text: applied attribute to fragment')

    # allow on_save call, to save helper file
    ed.set_prop(PROP_MODIFIED, True)


def item_to_color(l, n):

    if len(l)>n:
        s = l[n]
        return html_color_to_int(s) if s else COLOR_NONE
    else:
        return COLOR_NONE
    
def do_color(ed, index):

    items = ini_read(ini, 'colors', str(index), '').split(',')

    color_back = item_to_color(items, 0)
    color_font = item_to_color(items, 1)
    color_border = item_to_color(items, 2)
    styles = items[3] if len(items)>3 else ''

    attr = {
        'tag': TAG_UNIQ + index,
        'c_font': color_font,
        'c_back': color_back,
        'c_border': color_border,
        'styles': styles,
    }
    set_text_attribute(ed, attr)


def clear_style(ed, n):

    ed.set_prop(PROP_MODIFIED, True) # need on_save call
    ed.attr(MARKERS_DELETE_BY_TAG, TAG_UNIQ + n)


def clear_in_selection(ed):

    carets = ed.get_carets()
    if len(carets)!=1:
        msg_status('Need single caret')
        return

    x1, y1, x2, y2 = carets[0]
    if y2<0:
        msg_status('No selection')
        return

    if (y1, x1)>(y2, x2):
        x1, y1, x2, y2 = x2, y2, x1, y1

    marks = ed.attr(MARKERS_GET)
    if not marks:
        return

    cnt = 0
    for i in reversed(range(len(marks))):
        ntag, nx, ny, nlen, *_ = marks[i]
        if TAG_UNIQ<=ntag<TAG_MAX and (y1, x1)<=(ny, nx) and (ny, nx+nlen)<=(y2, x2):
            del marks[i]
            cnt += 1

    msg_status('Deleted %d attrib(s)'%cnt)
    if cnt:
        ed.set_prop(PROP_MODIFIED, True)

        for i in range(TAG_UNIQ, TAG_MAX):
            ed.attr(MARKERS_DELETE_BY_TAG, tag=i)

        for m in marks:
            ed.attr(MARKERS_ADD, *m)


def load_helper_file(ed):

    fn = ed.get_filename()
    if not fn: return

    fn_res = fn + HELPER_EXT
    if not os.path.isfile(fn_res):
        return

    with open(fn_res, 'r') as f:
        res = json.load(f)

    load_ops()

    for r in res:
        border = r.get('brd', '')
        ed.attr(MARKERS_ADD,
            tag = r['tag'],
            x = r['x'],
            y = r['y'],
            len = r['len'],
            color_font = r['c_font'],
            color_bg = r['c_bg'],
            color_border = r['c_border'],
            font_bold = 1 if r['f_b'] else 0,
            font_italic = 1 if r['f_i'] else 0,
            font_strikeout = 1 if r['f_s'] else 0,
            border_left = 1 if 'l' in border else 0,
            border_right = 1 if 'r' in border else 0,
            border_down = 1 if 'd' in border else 0,
            border_up = 1 if 'u' in border else 0,
            show_on_map = opt_show_on_map,
            map_only = (2 if opt_show_on_map else 0)
            )

    print('Color Text: restored %d attribs for "%s"' % (len(res), os.path.basename(fn)))


def save_helper_file(ed):

    fn = ed.get_filename()
    if not fn: return

    fn_res = fn + HELPER_EXT
    if os.path.isfile(fn_res):
        os.remove(fn_res)

    marks = ed.attr(MARKERS_GET)
    if not marks:
        return

    res = []
    for mark in marks:
        tag, x, y, len, color_font, color_bg, color_border, font_bold, font_italic, font_strikeout, b_l, b_r, b_d, b_u = mark[:14]
        border = ('l' if b_l else '') + ('r' if b_r else '') + ('d' if b_d else '') + ('u' if b_u else '')
        if TAG_UNIQ<=tag<=TAG_MAX:
            res.append({
                'tag': tag,
                'x': x,
                'y': y,
                'len': len,
                'c_font': color_font,
                'c_bg': color_bg,
                'c_border': color_border,
                'f_b': font_bold!=0,
                'f_i': font_italic!=0,
                'f_s': font_strikeout!=0,
                'brd': border,
                })

    if not res:
        return

    with open(fn_res, 'w') as f:
        json.dump(res, fp=f, indent=2)


class Command:

    def color1(self): do_color(ed, 1)
    def color2(self): do_color(ed, 2)
    def color3(self): do_color(ed, 3)
    def color4(self): do_color(ed, 4)
    def color5(self): do_color(ed, 5)
    def color6(self): do_color(ed, 6)

    def format_styles(self, styles):
        attr = {
            'tag': TAG_UNIQ,
            'c_font': COLOR_NONE, # ed.get_prop(PROP_COLOR, COLOR_ID_TextFont),
            'c_back': COLOR_NONE,
            'c_border': COLOR_NONE,
            'styles': styles,
        }
        set_text_attribute(ed, attr)

    def format_bold(self):
        self.format_styles('b')
    def format_italic(self):
        self.format_styles('i')
    def format_bold_italic(self):
        self.format_styles('bi')
    def format_strikeout(self):
        self.format_styles('s')

    def clear_all(self):
        for i in range(7):
            clear_style(ed, i)

    def clear_sel(self):
        clear_in_selection(ed)

    def clear1(self): clear_style(ed, 1)
    def clear2(self): clear_style(ed, 2)
    def clear3(self): clear_style(ed, 3)
    def clear4(self): clear_style(ed, 4)
    def clear5(self): clear_style(ed, 5)
    def clear6(self): clear_style(ed, 6)

    def config(self):
        ini_write(ini, 'op', 'all_words'      , bool_to_str(opt_all_words    ))
        ini_write(ini, 'op', 'whole_words'    , bool_to_str(opt_whole_words  ))
        ini_write(ini, 'op', 'case_sensitive' , bool_to_str(opt_case_sens    ))
        ini_write(ini, 'op', 'show_on_map'    , bool_to_str(opt_show_on_map  ))

        file_open(ini)

    def on_open(self, ed_self):
        load_helper_file(ed_self)

    def on_save(self, ed_self):
        save_helper_file(ed_self)
