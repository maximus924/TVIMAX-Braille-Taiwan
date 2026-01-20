# 檔案名稱: braille_converter.py (v18 數學大師版)
from pypinyin import pinyin, Style, load_phrases_dict
import braille_rules as rules 

# 預設破音字
default_polyphone_fixes = {
    '冠軍': [['guan4'], ['jun1']], 
    '皇冠': [['guan1'], ['guan1']], 
    '校對': [['jiao4'], ['dui4']],
    '重創': [['zhong4'], ['chuang1']],
    '創傷': [['chuang1'], ['shang1']],
    '了解': [['liao3'], ['jie3']],
    '艾璞樂': [['ai4'], ['pu2'], ['le4']],
    '錡銳': [['qi2'], ['rui4']],
}
load_phrases_dict(default_polyphone_fixes)

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

    # 自定義規則
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
    
    # Nemeth 狀態
    nemeth_context = 'LITERARY' 
    last_math_token = 'SPACE' # SPACE, NUMBER, OPERATION, COMPARISON, INDICATOR
    math_level = 0 # 0=基線, 1=上標

    while text_index < len(text):
        
        # 1. 直接替換
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

        # 2. 注音強制修正
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
                    char_braille, is_err = convert_single_char_zhuyin(char, user_zhuyin, rules)
                    full_braille += char_braille
                    dual_list.append({'char': char, 'braille': char_braille, 'is_error': is_err})
                text_index += len(word)
                is_number_mode = False
                match_bopomofo = True
                break
        if match_bopomofo: continue

        char = text[text_index]

        # === Nemeth 數學處理邏輯 ===
        if is_nemeth_mode:
            # 判斷是否為數學元素 (包含 ^ 和運算符)
            is_math_char = (
                char.isdigit() or 
                char in rules.NEMETH['OPERATION_SIGNS'] or 
                char in rules.NEMETH['COMPARISON_SIGNS'] or
                char in rules.NEMETH['PARENTHESES'] or
                char == '^'
            )
            
            if char == ' ': # 空格處理
                full_braille += " "
                dual_list.append({'char': ' ', 'braille': ' ', 'is_error': False})
                text_index += 1
                last_math_token = 'SPACE'
                continue

            if is_math_char:
                # 進入數學模式
                if nemeth_context == 'LITERARY':
                    if use_nemeth_indicators:
                        start_code = rules.NEMETH['SWITCH']['START']
                        full_braille += start_code
                        dual_list.append({'char': '', 'braille': start_code, 'is_error': False})
                    nemeth_context = 'MATH'
                    last_math_token = 'SPACE'
                    math_level = 0
                
                char_braille = ""
                
                # (A) 次方/上標符號 (^)
                if char == '^':
                    char_braille = rules.NEMETH['INDICATORS']['SUPERSCRIPT']
                    full_braille += char_braille
                    dual_list.append({'char': '^', 'braille': char_braille, 'is_error': False})
                    last_math_token = 'INDICATOR' # 上標後數字通常不加數符
                    math_level += 1
                    text_index += 1
                    continue

                # (B) 運算符號 (+ - * /)
                if char in rules.NEMETH['OPERATION_SIGNS']:
                    # 關鍵邏輯：如果在上標模式，遇到運算符號，要先回到基線！
                    if math_level > 0:
                        baseline_code = rules.NEMETH['INDICATORS']['BASELINE']
                        full_braille += baseline_code
                        dual_list.append({'char': '', 'braille': baseline_code, 'is_error': False})
                        math_level = 0 # 歸零
                    
                    char_braille = rules.NEMETH['OPERATION_SIGNS'][char]
                    last_math_token = 'OPERATION' # 運算符後不加數符
                    
                # (C) 比較符號 (= > <)
                elif char in rules.NEMETH['COMPARISON_SIGNS']:
                    if math_level > 0:
                        baseline_code = rules.NEMETH['INDICATORS']['BASELINE']
                        full_braille += baseline_code
                        dual_list.append({'char': '', 'braille': baseline_code, 'is_error': False})
                        math_level = 0
                    
                    char_braille = rules.NEMETH['COMPARISON_SIGNS'][char]
                    last_math_token = 'COMPARISON' # 比較符後要加數符

                # (D) 數字
                elif char.isdigit():
                    # 判斷是否省略數符
                    # 規則：前為運算符(OPERATION) 或 指標(INDICATOR, 含上標) 或 數字(NUMBER)，省略數符
                    # 前為比較符(COMPARISON) 或 空格(SPACE)，要加數符
                    if last_math_token in ['SPACE', 'COMPARISON', 'PUNCTUATION']:
                        char_braille += rules.NEMETH['INDICATORS']['NUMERIC']
                    
                    char_braille += rules.NEMETH['DIGITS'][char]
                    last_math_token = 'NUMBER'
                
                # (E) 括號
                elif char in rules.NEMETH['PARENTHESES']:
                    char_braille = rules.NEMETH['PARENTHESES'][char]
                    last_math_token = 'PUNCTUATION'
                
                full_braille += char_braille
                dual_list.append({'char': char, 'braille': char_braille, 'is_error': False})
                text_index += 1
                continue

            else:
                # 非數學字符 -> 切換回文字模式
                if nemeth_context == 'MATH':
                    if use_nemeth_indicators:
                        end_code = rules.NEMETH['SWITCH']['END']
                        full_braille += end_code
                        dual_list.append({'char': '', 'braille': end_code, 'is_error': False})
                    nemeth_context = 'LITERARY'
                    math_level = 0
                pass

        # === 標準文字處理 ===
        # 英文處理
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

        # 數字標準處理 (非 Nemeth)
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

        # 標點
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

        # 中文
        is_number_mode = False
        single_pinyin = pinyin(char, style=Style.BOPOMOFO)
        zhuyin = single_pinyin[0][0]
        char_braille, is_err = convert_single_char_zhuyin(char, zhuyin, rules)
        
        full_braille += char_braille
        dual_list.append({'char': char, 'braille': char_braille, 'is_error': is_err})
        text_index += 1

    if is_nemeth_mode and use_nemeth_indicators and nemeth_context == 'MATH':
        end_code = rules.NEMETH['SWITCH']['END']
        full_braille += end_code
        dual_list.append({'char': '', 'braille': end_code, 'is_error': False})

    return full_braille, dual_list

def convert_single_char_zhuyin(char, zhuyin, rules):
    # 邏輯不變
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

def generate_html_content(dual_data, chars_per_line, font_size_px):
    # 邏輯不變
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