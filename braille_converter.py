# 檔案名稱: braille_converter.py (v15 雙軌切換版)
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

# [新增參數] english_mode: 'UEB' 或 'Traditional'
def text_to_braille(text, custom_rules=None, english_mode='UEB'):
    full_braille = "" 
    dual_list = [] 
    
    # 根據模式選擇規則集
    if english_mode == 'UEB':
        current_punctuation = rules.PUNCTUATION_UEB
        current_special = rules.SPECIAL_UEB
    else:
        current_punctuation = rules.PUNCTUATION_TRADITIONAL
        current_special = rules.SPECIAL_TRADITIONAL

    # 強制數字表
    SAFE_NUMBER_MAP = {
        '1': '⠂', '2': '⠆', '3': '⠒', '4': '⠲', '5': '⠢',
        '6': '⠖', '7': '⠶', '8': '⠦', '9': '⠔', '0': '⠴'
    }

    braille_overrides = {} 
    bopomofo_overrides = {}

    if custom_rules:
        for key, value in custom_rules.items():
            if any(c in 'ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦˊˇˋ˙' for c in value):
                bopomofo_overrides[key] = value.split()
            else:
                braille_overrides[key] = value

    full_pinyin_list = pinyin(text, style=Style.BOPOMOFO)
    text_index = 0
    is_number_mode = False 
    
    while text_index < len(text):
        
        # 1. 直接替換
        match_override = False
        for word, braille_code in braille_overrides.items():
            if text.startswith(word, text_index):
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
                for i, char in enumerate(word):
                    user_zhuyin = bopomofo_list[i] if i < len(bopomofo_list) else ""
                    # 傳遞規則集進去 (雖然中文規則通常不變，但保持一致性)
                    char_braille, is_err = convert_single_char_zhuyin(char, user_zhuyin, rules)
                    full_braille += char_braille
                    dual_list.append({'char': char, 'braille': char_braille, 'is_error': is_err})
                text_index += len(word)
                is_number_mode = False
                match_bopomofo = True
                break
        if match_bopomofo: continue

        # 3. 英文單字偵測與處理
        current_segment = text[text_index]
        if 'a' <= text[text_index].lower() <= 'z':
            end_idx = text_index
            while end_idx < len(text) and ('a' <= text[end_idx].lower() <= 'z'):
                end_idx += 1
            current_segment = text[text_index : end_idx]
        
        # === 英文處理核心 ===
        if len(current_segment) > 0 and current_segment[0].lower() in rules.ENGLISH:
            is_number_mode = False
            
            # UEB 全大寫邏輯
            if english_mode == 'UEB':
                is_all_caps = current_segment.isupper() and len(current_segment) > 1
                prefix = current_special['WORD_CAP_SYMBOL'] if is_all_caps else ""
            else:
                # 傳統模式：通常全大寫比較少用雙點，或者看習慣。這裡我們先從簡，只標首字大寫
                # 或是如果使用者希望舊版也支援全大寫，可保留。
                # 這裡設定：舊版不自動合併全大寫符號，每個大寫字母自己標 (或依需求調整)
                is_all_caps = False 
                prefix = ""

            segment_braille_str = ""
            dual_items = []
            
            for i, char in enumerate(current_segment):
                c_braille = ""
                # 大寫處理
                if is_all_caps:
                    if i == 0: c_braille += prefix
                elif char.isupper():
                    c_braille += current_special['CAP_SYMBOL']
                
                c_braille += rules.ENGLISH[char.lower()]
                
                segment_braille_str += c_braille
                dual_items.append({'char': char, 'braille': c_braille, 'is_error': False})
            
            full_braille += segment_braille_str
            dual_list.extend(dual_items)
            text_index += len(current_segment)
            continue
            # ========================

        char = text[text_index]
        
        # 4. 數字與標點處理
        if not ('\u4e00' <= char <= '\u9fff'):
            char_braille = ""
            if char.isdigit():
                if not is_number_mode:
                    char_braille += current_special['NUMBER_PREFIX']
                    is_number_mode = True
                if char in SAFE_NUMBER_MAP:
                    char_braille += SAFE_NUMBER_MAP[char]
                elif char in current_punctuation:
                    char_braille += current_punctuation[char]
            elif char in current_punctuation:
                is_number_mode = False
                char_braille += current_punctuation[char]
            else:
                is_number_mode = False
                char_braille += char 
            
            full_braille += char_braille
            dual_list.append({'char': char, 'braille': char_braille, 'is_error': False})
            text_index += 1
            continue

        # 5. 中文處理
        is_number_mode = False
        single_pinyin = pinyin(char, style=Style.BOPOMOFO)
        zhuyin = single_pinyin[0][0]
        char_braille, is_err = convert_single_char_zhuyin(char, zhuyin, rules)
        
        full_braille += char_braille
        dual_list.append({'char': char, 'braille': char_braille, 'is_error': is_err})
        text_index += 1

    return full_braille, dual_list

def convert_single_char_zhuyin(char, zhuyin, rules):
    # 此函式邏輯不變
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
    # 此函式邏輯不變
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