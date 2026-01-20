# 檔案名稱: braille_converter.py (v17 智慧混排版)
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

# [新增參數] use_nemeth_indicators (預設 False)
def text_to_braille(text, custom_rules=None, mode='UEB', use_nemeth_indicators=False):
    """
    mode: 'UEB', 'Traditional', 'Nemeth'
    use_nemeth_indicators: 是否自動插入 Nemeth 起始/結束號
    """
    full_braille = "" 
    dual_list = [] 
    
    # 1. 初始化設定
    is_nemeth_mode = (mode == 'Nemeth')
    
    if mode == 'Traditional':
        current_punctuation = rules.PUNCTUATION_TRADITIONAL
        current_special = rules.SPECIAL_TRADITIONAL
    else: # UEB or Nemeth (literary part uses UEB base)
        current_punctuation = rules.PUNCTUATION_UEB
        current_special = rules.SPECIAL_UEB

    # 自定義規則解析
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
    
    # --- Nemeth 狀態機變數 ---
    # context: 'LITERARY' (文字) 或 'MATH' (數學)
    # 預設為 LITERARY
    nemeth_context = 'LITERARY' 
    last_math_token = 'SPACE' # 用於判斷省略數符 (SPACE, NUMBER, OPERATOR)

    while text_index < len(text):
        
        # --- 優先權 1: 直接替換 ---
        match_override = False
        for word, braille_code in braille_overrides.items():
            if text.startswith(word, text_index):
                # 強制替換視為文字或保留原狀態? 這裡簡單處理：視為文字
                # 如果在數學模式中，可能需要先結束數學?
                if is_nemeth_mode and use_nemeth_indicators and nemeth_context == 'MATH':
                    # 插入結束號
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

        # --- 優先權 2: 注音強制修正 ---
        match_bopomofo = False
        for word, bopomofo_list in bopomofo_overrides.items():
            if text.startswith(word, text_index):
                # 切換回文字模式
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

        # === 核心邏輯 ===
        if is_nemeth_mode:
            # 判斷這個字是不是「數學元素」
            # 數學元素：數字、Nemeth運算符號、Nemeth括號
            is_math_char = (
                char.isdigit() or 
                char in rules.NEMETH['OPERATORS'] or 
                char in rules.NEMETH['PARENTHESES']
            )
            
            # 特殊：空格通常延續上一個狀態，不觸發切換
            if char == ' ':
                # 保持原狀態，直接輸出空格
                full_braille += " "
                dual_list.append({'char': ' ', 'braille': ' ', 'is_error': False})
                text_index += 1
                # 更新 last_math_token 為 SPACE，這樣下一個數字會加數符
                last_math_token = 'SPACE' 
                continue

            # --- 狀態切換偵測 ---
            if is_math_char:
                # 如果現在是文字模式，要切換到數學模式
                if nemeth_context == 'LITERARY':
                    if use_nemeth_indicators:
                        start_code = rules.NEMETH['SWITCH']['START']
                        full_braille += start_code
                        dual_list.append({'char': '', 'braille': start_code, 'is_error': False})
                    nemeth_context = 'MATH'
                    last_math_token = 'SPACE' # 重置數學狀態
                
                # 執行 Nemeth 轉譯
                char_braille = ""
                
                # (A) 數字
                if char.isdigit():
                    # 判斷是否需要數符
                    # 規則：如果前面是 SPACE 或 PUNCTUATION (非運算符)，加數符
                    if last_math_token in ['SPACE', 'PUNCTUATION', 'CHAR']: 
                        char_braille += rules.NEMETH['INDICATORS']['NUMERIC']
                    char_braille += rules.NEMETH['DIGITS'][char]
                    last_math_token = 'NUMBER'
                
                # (B) 運算符
                elif char in rules.NEMETH['OPERATORS']:
                    char_braille += rules.NEMETH['OPERATORS'][char]
                    last_math_token = 'OPERATOR'
                
                # (C) 括號
                elif char in rules.NEMETH['PARENTHESES']:
                    char_braille += rules.NEMETH['PARENTHESES'][char]
                    last_math_token = 'PUNCTUATION'
                
                full_braille += char_braille
                dual_list.append({'char': char, 'braille': char_braille, 'is_error': False})
                text_index += 1
                continue
            
            else:
                # 這是「非數學元素」 (例如中文、一般標點、英文單字)
                # 如果現在是數學模式，要切換回文字模式
                if nemeth_context == 'MATH':
                    if use_nemeth_indicators:
                        end_code = rules.NEMETH['SWITCH']['END']
                        full_braille += end_code
                        dual_list.append({'char': '', 'braille': end_code, 'is_error': False})
                    nemeth_context = 'LITERARY'
                
                # 接下來交給下方的標準流程處理 (Standard Literary Process)
                pass 

        # === 標準文字處理流程 (Literary) ===
        # 英文偵測
        current_segment = text[text_index]
        if 'a' <= text[text_index].lower() <= 'z':
            end_idx = text_index
            while end_idx < len(text) and ('a' <= text[end_idx].lower() <= 'z'):
                end_idx += 1
            current_segment = text[text_index : end_idx]
        
        if len(current_segment) > 0 and current_segment[0].lower() in rules.ENGLISH:
            # 英文處理 (同前)
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

        # 數字標準處理 (非 Nemeth 模式下的數字)
        if char.isdigit():
            # 注意：如果上面 Nemeth 邏輯已經處理過，這裡不會執行到 (因為 if is_math_char continue 了)
            # 這裡處理的是「不在 Nemeth 模式」或「Nemeth 模式判定為文字」的情況
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

        # 標點處理
        if char in current_punctuation:
            is_number_mode = False
            cb = current_punctuation[char]
            full_braille += cb
            dual_list.append({'char': char, 'braille': cb, 'is_error': False})
            text_index += 1
            continue
            
        if char == ' ':
            # 這裡處理非 Nemeth 的空格，或者已切換回 Literary 的空格
            is_number_mode = False
            full_braille += " " # 顯示空格
            dual_list.append({'char': ' ', 'braille': ' ', 'is_error': False})
            text_index += 1
            continue

        # 中文處理
        is_number_mode = False
        single_pinyin = pinyin(char, style=Style.BOPOMOFO)
        zhuyin = single_pinyin[0][0]
        char_braille, is_err = convert_single_char_zhuyin(char, zhuyin, rules)
        
        full_braille += char_braille
        dual_list.append({'char': char, 'braille': char_braille, 'is_error': is_err})
        text_index += 1

    # 迴圈結束後，如果還在數學模式，要記得關閉
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