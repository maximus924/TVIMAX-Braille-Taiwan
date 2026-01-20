import streamlit as st
from pypinyin import pinyin, Style, load_phrases_dict
import time

# ==========================================
# 1. 規則定義 (直接寫在這裡，不再依賴外部檔案)
# ==========================================
class BrailleRules:
    # 聲母
    INITIALS = {
        'ㄅ': '⠕', 'ㄆ': '⠏', 'ㄇ': '⠍', 'ㄈ': '⠟',
        'ㄉ': '⠙', 'ㄊ': '⠋', 'ㄋ': '⠝', 'ㄌ': '⠉',
        'ㄍ': '⠅', 'ㄎ': '⠇', 'ㄏ': '⠗',
        'ㄐ': '⠅', 'ㄑ': '⠚', 'ㄒ': '⠑',
        'ㄓ': '⠁', 'ㄔ': '⠃', 'ㄕ': '⠊', 'ㄖ': '⠛',
        'ㄗ': '⠓', 'ㄘ': '⠚', 'ㄙ': '⠑'
    }
    ZI_CHI_SHI_RI_GROUPS = {'ㄓ', 'ㄔ', 'ㄕ', 'ㄖ', 'ㄗ', 'ㄘ', 'ㄙ'}

    # 韻母
    FINALS = {
        'ㄚ': '⠜', 'ㄛ': '⠣', 'ㄜ': '⠮', 'ㄝ': '⠢',
        'ㄞ': '⠺', 'ㄟ': '⠴', 'ㄠ': '⠩', 'ㄡ': '⠷',
        'ㄢ': '⠧', 'ㄣ': '⠥', 'ㄤ': '⠭', 'ㄥ': '⠵',
        'ㄦ': '⠱', 'ㄧ': '⠡', 'ㄨ': '⠌', 'ㄩ': '⠳'
    }

    # 結合韻
    COMBINED_FINALS = {
        'ㄧㄚ': '⠾', 'ㄨㄚ': '⠔', 'ㄧㄛ': '⠴', 'ㄨㄛ': '⠒',
        'ㄧㄝ': '⠬', 'ㄩㄝ': '⠦', 'ㄧㄞ': '⠢', 'ㄨㄞ': '⠶',
        'ㄨㄟ': '⠫', 'ㄧㄠ': '⠪', 'ㄧㄡ': '⠎', 'ㄧㄢ': '⠞',
        'ㄨㄢ': '⠻', 'ㄩㄢ': '⠘', 'ㄧㄣ': '⠹', 'ㄨㄣ': '⠿',
        'ㄩㄣ': '⠲', 'ㄧㄤ': '⠨', 'ㄨㄤ': '⠸', 'ㄧㄥ': '⠽',
        'ㄨㄥ': '⠯', 'ㄩㄥ': '⠖'
    }

    # 聲調
    TONES = {1: '⠄', 'ˊ': '⠂', 'ˇ': '⠈', 'ˋ': '⠐', '˙': '⠁', 5: '⠁'}

    # 標點符號 (一般)
    PUNCTUATION_BASE = {
        '，': '⠆', ',': '⠆', '、': '⠠', '；': '⠰', ';': '⠰',
        '：': '⠒⠒', ':': '⠒⠒', '。': '⠤', '.': '⠤',
        '？': '⠕', '?': '⠕', '！': '⠇', '!': '⠇',
        '「': '⠰⠤', '」': '⠤⠆', '【': '⠯', ']': '⠽',
        '『': '⠰⠤', '』': '⠤⠆', '—': '⠒⠒', '-': '⠒',
        '（': '⠪', '）': '⠕'
    }
    PUNCTUATION_TRADITIONAL = PUNCTUATION_BASE.copy()
    PUNCTUATION_TRADITIONAL.update({'(': '⠪', ')': '⠕', '[': '⠯', ']': '⠽'})
    PUNCTUATION_UEB = PUNCTUATION_BASE.copy()
    PUNCTUATION_UEB.update({'(': '⠐⠣', ')': '⠐⠜', '[': '⠨⠣', ']': '⠨⠜'})

    # 特殊符號
    SPECIAL_TRADITIONAL = {'NUMBER_PREFIX': '⠼', 'CAP_SYMBOL': '⠠', 'WORD_CAP_SYMBOL': '⠠⠠', 'SPACE': '  '}
    SPECIAL_UEB = {'NUMBER_PREFIX': '⠼', 'CAP_SYMBOL': '⠠', 'WORD_CAP_SYMBOL': '⠠⠠', 'SPACE': '  '}

    # 英文
    ENGLISH = {
        'a': '⠁', 'b': '⠃', 'c': '⠉', 'd': '⠙', 'e': '⠑', 'f': '⠋', 'g': '⠛', 'h': '⠓', 'i': '⠊', 'j': '⠚',
        'k': '⠅', 'l': '⠇', 'm': '⠍', 'n': '⠝', 'o': '⠕', 'p': '⠏', 'q': '⠟', 'r': '⠗', 's': '⠎', 't': '⠞',
        'u': '⠥', 'v': '⠧', 'w': '⠺', 'x': '⠭', 'y': '⠽', 'z': '⠵'
    }

    # Nemeth 數學符號庫 (完整版)
    NEMETH = {
        'DIGITS': {
            '1': '⠂', '2': '⠆', '3': '⠒', '4': '⠲', '5': '⠢',
            '6': '⠖', '7': '⠶', '8': '⠦', '9': '⠔', '0': '⠴'
        },
        'OPERATION_SIGNS': {
            '+': '⠬', '-': '⠤', '×': '⠈⠡', '*': '⠈⠡', '÷': '⠨⠌', '/': '⠨⠌'
        },
        'COMPARISON_SIGNS': {
            '=': '⠀⠨⠅⠀', '>': '⠀⠨⠂⠀', '<': '⠀⠐⠅⠀'
        },
        'MATH_KEYWORDS': {
            '加': '+', '＋': '+',
            '減': '-', '－': '-', '負': '-', 
            '乘以': '×', '乘': '×',
            '除以': '÷', '除': '÷',
            '等於': '=', '＝': '=',
            '：': ':', '.': '.'
        },
        'INDICATORS': {
            'NUMERIC': '⠼', 'SUPERSCRIPT': '⠘', 'BASELINE': '⠐', 'SPACE': ' '
        },
        'PARENTHESES': {
            '(': '⠷', ')': '⠾', '[': '⠨⠷', ']': '⠨⠾', '{': '⠸⠷', '}': '⠸⠾',
            '（': '⠷', '）': '⠾'
        },
        'SWITCH': {
            'START': '⠸⠩⠀', 'END': '⠀⠸⠱'
        }
    }

# 初始化規則物件
rules = BrailleRules()

# ==========================================
# 2. 轉譯引擎邏輯
# ==========================================

# 預設破音字
default_polyphone_fixes = {
    '冠軍': [['guan4'], ['jun1']], '皇冠': [['guan1'], ['guan1']], 
    '校對': [['jiao4'], ['dui4']], '重創': [['zhong4'], ['chuang1']],
    '創傷': [['chuang1'], ['shang1']], '了解': [['liao3'], ['jie3']],
    '艾璞樂': [['ai4'], ['pu2'], ['le4']], '錡銳': [['qi2'], ['rui4']],
}
load_phrases_dict(default_polyphone_fixes)

def convert_single_char_zhuyin(char, zhuyin):
    sheng = ""
    yun = ""
    tone = ""
    is_error = False 
    temp_zhuyin = zhuyin
    
    if temp_zhuyin and temp_zhuyin[-1] in rules.TONES:
        tone = rules.TONES[temp_zhuyin[-1]]
        temp_zhuyin = temp_zhuyin[:-1] 
    elif '˙' in temp_zhuyin:
            tone = rules.TONES[5]
            temp_zhuyin = temp_zhuyin.replace('˙', '')
    else:
        tone = rules.TONES[1]

    for initial in rules.INITIALS:
        if temp_zhuyin.startswith(initial):
            sheng = rules.INITIALS[initial]
            temp_zhuyin = temp_zhuyin[len(initial):]
            break
    
    if temp_zhuyin in rules.COMBINED_FINALS:
        yun = rules.COMBINED_FINALS[temp_zhuyin]
    elif temp_zhuyin in rules.FINALS:
        yun = rules.FINALS[temp_zhuyin]
        
    if sheng and not yun:
            if not temp_zhuyin and zhuyin[0] in rules.ZI_CHI_SHI_RI_GROUPS:
                yun = rules.FINALS['ㄦ']
    
    if not yun: is_error = True
    return sheng + yun + tone, is_error

def text_to_braille(text, custom_rules=None, mode='UEB', use_nemeth_indicators=False):
    full_braille = "" 
    dual_list = [] 
    is_nemeth_mode = (mode == 'Nemeth')
    
    if mode == 'Traditional':
        current_punctuation = rules.PUNCTUATION_TRADITIONAL
        current_special = rules.SPECIAL_TRADITIONAL
    else: 
        current_punctuation = rules.PUNCTUATION_UEB
        current_special = rules.SPECIAL_UEB

    braille_overrides = {} 
    bopomofo_overrides = {}
    if custom_rules:
        for key, value in custom_rules.items():
            if any(c in 'ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦˊˇˋ˙' for c in value):
                bopomofo_overrides[key] = value.split()
            else:
                braille_overrides[key] = value

    text_index = 0
    is_number_mode = False 
    nemeth_context = 'LITERARY' 
    last_math_token = 'SPACE' 
    math_level = 0 

    while text_index < len(text):
        match_override = False
        for word, braille_code in braille_overrides.items():
            if text.startswith(word, text_index):
                if is_nemeth_mode and use_nemeth_indicators and nemeth_context == 'MATH':
                    end_code = rules.NEMETH['SWITCH']['END']
                    full_braille += end_code
                    dual_list.append({'char': '', 'braille': end_code, 'is_error': False})
                    nemeth_context = 'LITERARY'
                full_braille += braille_code
                dual_list.append({'char': word, 'braille': braille_code, 'is_error': False})
                text_index += len(word)
                is_number_mode = False
                match_override = True
                break
        if match_override: continue

        match_bopomofo = False
        for word, bopomofo_list in bopomofo_overrides.items():
            if text.startswith(word, text_index):
                if is_nemeth_mode and use_nemeth_indicators and nemeth_context == 'MATH':
                    end_code = rules.NEMETH['SWITCH']['END']
                    full_braille += end_code
                    dual_list.append({'char': '', 'braille': end_code, 'is_error': False})
                    nemeth_context = 'LITERARY'
                for i, char in enumerate(word):
                    user_zhuyin = bopomofo_list[i] if i < len(bopomofo_list) else ""
                    char_braille, is_err = convert_single_char_zhuyin(char, user_zhuyin)
                    full_braille += char_braille
                    dual_list.append({'char': char, 'braille': char_braille, 'is_error': is_err})
                text_index += len(word)
                is_number_mode = False
                match_bopomofo = True
                break
        if match_bopomofo: continue

        char = text[text_index]

        # === Nemeth Logic ===
        if is_nemeth_mode:
            mapped_char = None
            if char in rules.NEMETH['MATH_KEYWORDS']:
                mapped_char = rules.NEMETH['MATH_KEYWORDS'][char]
            
            target_char = mapped_char if mapped_char else char
            
            is_math_char = (
                char.isdigit() or 
                target_char in rules.NEMETH['OPERATION_SIGNS'] or 
                target_char in rules.NEMETH['COMPARISON_SIGNS'] or
                target_char in rules.NEMETH['PARENTHESES'] or
                target_char == '^'
            )
            
            if char == ' ': 
                full_braille += " "
                dual_list.append({'char': ' ', 'braille': ' ', 'is_error': False})
                text_index += 1
                last_math_token = 'SPACE'
                continue

            if is_math_char:
                if nemeth_context == 'LITERARY':
                    if use_nemeth_indicators:
                        start_code = rules.NEMETH['SWITCH']['START']
                        full_braille += start_code
                        dual_list.append({'char': '', 'braille': start_code, 'is_error': False})
                    nemeth_context = 'MATH'
                    last_math_token = 'SPACE'
                    math_level = 0
                
                char_braille = ""
                if target_char == '^':
                    char_braille = rules.NEMETH['INDICATORS']['SUPERSCRIPT']
                    full_braille += char_braille
                    dual_list.append({'char': char, 'braille': char_braille, 'is_error': False})
                    last_math_token = 'INDICATOR'
                    math_level += 1
                    text_index += 1
                    continue

                if target_char in rules.NEMETH['OPERATION_SIGNS']:
                    if math_level > 0:
                        baseline_code = rules.NEMETH['INDICATORS']['BASELINE']
                        full_braille += baseline_code
                        dual_list.append({'char': '', 'braille': baseline_code, 'is_error': False})
                        math_level = 0
                    char_braille = rules.NEMETH['OPERATION_SIGNS'][target_char]
                    last_math_token = 'OPERATION'
                elif target_char in rules.NEMETH['COMPARISON_SIGNS']:
                    if math_level > 0:
                        baseline_code = rules.NEMETH['INDICATORS']['BASELINE']
                        full_braille += baseline_code
                        dual_list.append({'char': '', 'braille': baseline_code, 'is_error': False})
                        math_level = 0
                    char_braille = rules.NEMETH['COMPARISON_SIGNS'][target_char]
                    last_math_token = 'COMPARISON'
                elif char.isdigit():
                    if last_math_token in ['SPACE', 'COMPARISON', 'PUNCTUATION']:
                        char_braille += rules.NEMETH['INDICATORS']['NUMERIC']
                    char_braille += rules.NEMETH['DIGITS'][char]
                    last_math_token = 'NUMBER'
                elif target_char in rules.NEMETH['PARENTHESES']:
                    char_braille = rules.NEMETH['PARENTHESES'][target_char]
                    last_math_token = 'PUNCTUATION'
                
                full_braille += char_braille
                dual_list.append({'char': char, 'braille': char_braille, 'is_error': False})
                text_index += 1
                continue
            else:
                if nemeth_context == 'MATH':
                    if use_nemeth_indicators:
                        end_code = rules.NEMETH['SWITCH']['END']
                        full_braille += end_code
                        dual_list.append({'char': '', 'braille': end_code, 'is_error': False})
                    nemeth_context = 'LITERARY'
                    math_level = 0
                pass

        # === Literary Logic ===
        current_segment = text[text_index]
        if 'a' <= text[text_index].lower() <= 'z':
            end_idx = text_index
            while end_idx < len(text) and ('a' <= text[end_idx].lower() <= 'z'):
                end_idx += 1
            current_segment = text[text_index : end_idx]
        
        if len(current_segment) > 0 and current_segment[0].lower() in rules.ENGLISH:
            is_number_mode = False
            is_all_caps = (mode == 'UEB') and current_segment.isupper() and len(current_segment) > 1
            prefix = current_special['WORD_CAP_SYMBOL'] if is_all_caps else ""
            segment_str = ""
            dual_items = []
            for i, c in enumerate(current_segment):
                cb = ""
                if is_all_caps:
                    if i == 0: cb += prefix
                elif c.isupper():
                    cb += current_special['CAP_SYMBOL']
                cb += rules.ENGLISH[c.lower()]
                segment_str += cb
                dual_items.append({'char': c, 'braille': cb, 'is_error': False})
            full_braille += segment_str
            dual_list.extend(dual_items)
            text_index += len(current_segment)
            continue

        if char.isdigit():
            cb = ""
            if not is_number_mode:
                cb += current_special['NUMBER_PREFIX']
                is_number_mode = True
            SAFE_MAP = {'1':'⠂','2':'⠆','3':'⠒','4':'⠲','5':'⠢','6':'⠖','7':'⠶','8':'⠦','9':'⠔','0':'⠴'}
            if char in SAFE_MAP: cb += SAFE_MAP[char]
            else: cb += char
            full_braille += cb
            dual_list.append({'char': char, 'braille': cb, 'is_error': False})
            text_index += 1
            continue

        if char in current_punctuation:
            is_number_mode = False
            cb = current_punctuation[char]
            full_braille += cb
            dual_list.append({'char': char, 'braille': cb, 'is_error': False})
            text_index += 1
            continue
            
        if char == ' ':
            is_number_mode = False
            full_braille += " "
            dual_list.append({'char': ' ', 'braille': ' ', 'is_error': False})
            text_index += 1
            continue

        is_number_mode = False
        single_pinyin = pinyin(char, style=Style.BOPOMOFO)
        zhuyin = single_pinyin[0][0]
        char_braille, is_err = convert_single_char_zhuyin(char, zhuyin)
        
        full_braille += char_braille
        dual_list.append({'char': char, 'braille': char_braille, 'is_error': is_err})
        text_index += 1

    if is_nemeth_mode and use_nemeth_indicators and nemeth_context == 'MATH':
        end_code = rules.NEMETH['SWITCH']['END']
        full_braille += end_code
        dual_list.append({'char': '', 'braille': end_code, 'is_error': False})

    return full_braille, dual_list

def generate_html_content(dual_data, chars_per_line, font_size_px):
    html_parts = ['<div class="braille-container">']
    current_line_len = 0
    for item in dual_data:
        char = item['char']
        braille = item['braille']
        is_error = item.get('is_error', False)
        b_len = len(braille)
        if current_line_len + b_len > chars_per_line:
            html_parts.append('<div class="break-line"></div>')
            current_line_len = 0
        box_class = "braille-box error-box" if is_error else "braille-box"
        box_html = f'<div class="{box_class}"><div class="char-top">{char}</div><div class="braille-bottom" style="font-size: {font_size_px}px;">{braille}</div></div>'
        html_parts.append(box_html)
        current_line_len += b_len
        if char == '\n':
             html_parts.append('<div class="break-line"></div>')
             current_line_len = 0
    html_parts.append('</div>')
    return "".join(html_parts)

# ==========================================
# 3. Streamlit 介面
# ========================================== 
st.set_page_config(page_title="麥西家正體中文字點字即時轉譯小麥麥(V20)", layout="wide")

st.markdown("""
<style>
    .braille-container { display: flex; flex-wrap: wrap; gap: 8px; padding: 15px; background-color: #f8f9fa; border-radius: 8px; border: 1px solid #e9ecef; line-height: 1.5; }
    .braille-box { display: flex; flex-direction: column; align-items: center; justify-content: center; border: 1px solid #ced4da; background-color: white; border-radius: 4px; padding: 4px; min-width: 32px; margin-bottom: 5px; }
    .error-box { border: 2px solid #ff4b4b !important; background-color: #ffe6e6 !important; }
    .char-top { font-size: 14px; color: #495057; margin-bottom: 2px; font-family: "Microsoft JhengHei", sans-serif; }
    .braille-bottom { font-weight: bold; color: #000; }
    .break-line { flex-basis: 100%; height: 0; margin: 0; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 設定與修正")
    st.info("系統狀態：All-in-One V20 無依賴版 🟢")
    st.divider()

    st.subheader("📝 我的詞庫")
    default_dict = "Boyan=⠠⠃⠕⠽⠁⠝\n快樂=ㄎㄨㄞˋ ㄌㄜˋ\n冠軍=ㄍㄨㄢˋ ㄐㄩㄣ"
    custom_dict_str = st.text_area("在此輸入自定義規則", value=default_dict, height=150)
    
    custom_rules = {}
    if custom_dict_str:
        for line in custom_dict_str.split('\n'):
            if '=' in line:
                k, v = line.split('=', 1)
                custom_rules[k.strip()] = v.strip()

    st.divider()
    st.subheader("🔠 轉譯模式")
    mode_option = st.radio("選擇內容類型：", ["UEB (統一英文點字)", "Traditional (傳統/舊版點字)", "Nemeth (聶美茲數學點字)"], index=0)
    
    if "Nemeth" in mode_option:
        mode = "Nemeth"
    elif "UEB" in mode_option:
        mode = "UEB"
    else:
        mode = "Traditional"

    use_nemeth_indicators = False
    if mode == "Nemeth":
        st.write("📐 **數學模式設定**")
        use_nemeth_indicators = st.checkbox("自動加入起始/結束號 (⠸⠩ ... ⠸⠱)", value=True)

    st.subheader("📄 排版設定")
    chars_per_line = st.number_input("每行方數", min_value=10, max_value=60, value=32)
    font_size_px = st.slider("字體大小", 12, 36, 22)

st.title("麥西家正體中文字點字即時轉譯小麥麥")
st.markdown("支援：全形轉半形、英文 UEB/傳統切換、**Nemeth 中數混排**、即時破音字修正")

st.header("輸入文字")
input_text = st.text_area("請在此貼上文章...", height=150, placeholder="例如：計算 1+2=3 的答案。")

if input_text:
    full_result, dual_data = text_to_braille(input_text, custom_rules, mode, use_nemeth_indicators)
    
    st.subheader("點字輸出 ⠒")
    st.text_area("純點字", value=full_result, height=150)
    
    c1, c2 = st.columns([1, 1])
    with c1:
        st.download_button("📥 下載 .txt", full_result, "braille_output.txt")
    
    html_content = generate_html_content(dual_data, chars_per_line, font_size_px)
    
    full_html_file = f"""<html><head><meta charset="utf-8"><style>.braille-container {{ display: flex; flex-wrap: wrap; gap: 5px; }}.braille-box {{ border: 1px solid #ccc; padding: 5px; margin: 2px; text-align: center; }}.braille-bottom {{ font-size: {font_size_px}px; font-weight: bold; }}.break-line {{ flex-basis: 100%; height: 0; }}</style></head><body><h2>雙視對照表</h2>{html_content}</body></html>"""
    
    with c2:
        st.download_button("🌏 下載 .html", full_html_file, "dual_view.html", mime="text/html")

    st.divider()
    st.header("雙視校對區")
    st.markdown(html_content, unsafe_allow_html=True)

