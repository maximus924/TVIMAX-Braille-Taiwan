# 檔案名稱: braille_converter.py (v20 多字詞辨識引擎)
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
    last_math_token = 'SPACE' 
    math_level = 0 

    # 預先準備排序好的關鍵字列表 (由長到短，避免 "大於等於" 被誤判為 "大於")
    sorted_math_keywords = []
    if is_nemeth_mode:
        sorted_math_keywords = sorted(rules.NEMETH['MATH_KEYWORDS'].keys(), key=len, reverse=True)

    while text_index < len(text):
        
        # 1. 直接替換 (User Custom)
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

        # === Nemeth 數學處理邏輯 (V20) ===
        if is_nemeth_mode:
            
            # [關鍵升級] 優先檢查多字詞的數學關鍵字 (如 "大於等於")
            found_keyword = None
            keyword_braille_or_symbol = None
            
            for kw in sorted_math_keywords:
                if text.startswith(kw, text_index):
                    found_keyword = kw
                    keyword_braille_or_symbol = rules.NEMETH['MATH_KEYWORDS'][kw]
                    break
            
            char = text[text_index] # 當前字元 (如果沒對應到關鍵字)
            
            # 決定當前要處理的內容是 關鍵字(多字) 還是 單字
            current_processing_text = found_keyword if found_keyword else char
            
            # 判斷是否為數學元素
            # 如果是關鍵字 -> 必為數學元素 (除了少數可能只是純符號轉換，這裡假設關鍵字都是數學相關)
            # 如果是單字 -> 檢查是否為數字、運算符等
            
            target_symbol = keyword_braille_or_symbol if found_keyword else char
            
            is_math_char = (
                found_keyword is not None or
                char.isdigit() or 
                char in rules.NEMETH['OPERATION_SIGNS'] or 
                char in rules.NEMETH['COMPARISON_SIGNS'] or
                char in rules.NEMETH['PARENTHESES'] or
                char == '^'
            )
            
            # 空格處理
            if not found_keyword and char == ' ': 
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
                
                # 判斷 target_symbol 是「點字碼」還是「需要進一步轉換的符號」
                # 我們約定：MATH_KEYWORDS 裡如果對應到 ASCII 運算符 (+ - =)，就繼續走邏輯
                # 如果對應到點字字串 (如 ⠫⠞)，就直接輸出
                
                # (X) 直接是點字碼 (例如 三角形、根號、中文關鍵字轉成的點字)
                # 簡單判斷法：看 target_symbol 是否包含點字 unicode (U+2800-U+28FF)
                # 或者它不在我們的運算符號字典裡
                is_direct_braille = any('\u2800' <= c <= '\u28ff' for c in target_symbol)
                
                if is_direct_braille:
                    # 特殊處理：如果是上標指示符 (如 "平方" -> ⠘⠆)
                    if target_symbol.startswith(rules.NEMETH['INDICATORS']['SUPERSCRIPT']):
                         math_level += 1
                         last_math_token = 'INDICATOR'
                    
                    # 輸出
                    char_braille = target_symbol
                    full_braille += char_braille
                    dual_list.append({'char': current_processing_text, 'braille': char_braille, 'is_error': False})
                    
                    # 狀態更新 (簡單假設大多是符號或數字類，這裡設為 CHAR 或 INDICATOR 較安全)
                    # 如果是"等於"的點字，應該視為 COMPARISON?
                    # 為了精準，如果它等於 COMPARISON_SIGNS 裡的值，設為 COMPARISON
                    if target_symbol in rules.NEMETH['COMPARISON_SIGNS'].values():
                         last_math_token = 'COMPARISON'
                    else:
                         last_math_token = 'CHAR' # 預設
                         
                    text_index += len(current_processing_text)
                    continue

                # (A) 次方 (^)
                if target_symbol == '^':
                    char_braille = rules.NEMETH['INDICATORS']['SUPERSCRIPT']
                    full_braille += char_braille
                    dual_list.append({'char': '^', 'braille': char_braille, 'is_error': False})
                    last_math_token = 'INDICATOR'
                    math_level += 1
                    text_index += 1
                    continue

                # (B) 運算符號
                if target_symbol in rules.NEMETH['OPERATION_SIGNS']:
                    if math_level > 0:
                        baseline_code = rules.NEMETH['INDICATORS']['BASELINE']
                        full_braille += baseline_code
                        dual_list.append({'char': '', 'braille': baseline_code, 'is_error': False})
                        math_level = 0
                    
                    char_braille = rules.NEMETH['OPERATION_SIGNS'][target_symbol]
                    last_math_token = 'OPERATION'
                    full_braille += char_braille
                    dual_list.append({'char': current_processing_text, 'braille': char_braille, 'is_error': False})
                    text_index += len(current_processing_text)
                    continue
                    
                # (C) 比較符號
                elif target_symbol in rules.NEMETH['COMPARISON_SIGNS']:
                    if math_level > 0:
                        baseline_code = rules.NEMETH['INDICATORS']['BASELINE']
                        full_braille += baseline_code
                        dual_list.append({'char': '', 'braille': baseline_code, 'is_error': False})
                        math_level = 0
                    
                    char_braille = rules.NEMETH['COMPARISON_SIGNS'][target_symbol]
                    last_math_token = 'COMPARISON'
                    full_braille += char_braille
                    dual_list.append({'char': current_processing_text, 'braille': char_braille, 'is_error': False})
                    text_index += len(current_processing_text)
                    continue

                # (D) 數字
                elif target_symbol.isdigit():
                    if last_math_token in ['SPACE', 'COMPARISON', 'PUNCTUATION', 'CHAR']:
                        char_braille += rules.NEMETH['INDICATORS']['NUMERIC']
                    char_braille += rules.NEMETH['DIGITS'][target_symbol]
                    last_math_token = 'NUMBER'
                    full_braille += char_braille
                    dual_list.append({'char': target_symbol, 'braille': char_braille, 'is_error': False})
                    text_index += 1
                    continue
                
                # (E) 括號
                elif target_symbol in rules.NEMETH['PARENTHESES']:
                    char_braille = rules.NEMETH['PARENTHESES'][target_symbol]
                    last_math_token = 'PUNCTUATION'
                    full_braille += char_braille
                    dual_list.append({'char': current_processing_text, 'braille': char_braille, 'is_error': False})
                    text_index += len(current_processing_text)
                    continue
                
                # 防呆：如果是其他符號但被標記為數學
                else:
                    text_index += len(current_processing_text)
                    continue

            else:
                # 非數學字符
                if nemeth_context == 'MATH':
                    if use_nemeth_indicators:
                        end_code = rules.NEMETH['SWITCH']['END']
                        full_braille += end_code
                        dual_list.append({'char': '', 'braille': end_code, 'is_error': False})
                    nemeth_context = 'LITERARY'
                    math_level = 0
                pass

        # === 標準文字處理 ===
        char = text[text_index] # 重新抓取，因為可能不是關鍵字
        
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