# 檔案名稱: braille_converter.py (v12 注音強制優先版)
from pypinyin import pinyin, Style, load_phrases_dict
import braille_rules as rules 

# 預設破音字 (保留給沒設定時使用)
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

def text_to_braille(text, custom_rules=None):
    full_braille = "" 
    dual_list = [] 
    
    # 強制顯示數字表
    SAFE_NUMBER_MAP = {
        '1': '⠂', '2': '⠆', '3': '⠒', '4': '⠲', '5': '⠢',
        '6': '⠖', '7': '⠶', '8': '⠦', '9': '⠔', '0': '⠴'
    }

    # --- 1. 解析自定義規則 ---
    braille_overrides = {} # 直接替換 (Boyan -> 點字)
    bopomofo_overrides = {} # 注音強制修正 (冠軍 -> ㄍㄨㄢˋ ㄐㄩㄣ)

    if custom_rules:
        temp_pinyin_fixes = {}
        for key, value in custom_rules.items():
            # 判斷值是否包含注音符號
            if any(c in 'ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦˊˇˋ˙' for c in value):
                # 存入 bopomofo_overrides，稍後手動處理
                # 使用 split() 將 "ㄍㄨㄢˋ ㄐㄩㄣ" 切割成 ['ㄍㄨㄢˋ', 'ㄐㄩㄣ']
                bopomofo_overrides[key] = value.split()
            else:
                braille_overrides[key] = value

    # 取得標準注音列表 (作為備用)
    full_pinyin_list = pinyin(text, style=Style.BOPOMOFO)
    
    text_index = 0
    is_number_mode = False 
    
    # 這裡我們改用 while 迴圈，方便靈活控制索引
    while text_index < len(text):
        
        # --- 2. 檢查是否命中「直接點字替換」規則 ---
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

        # --- 3. [關鍵新增] 檢查是否命中「注音強制修正」規則 ---
        match_bopomofo = False
        for word, bopomofo_list in bopomofo_overrides.items():
            if text.startswith(word, text_index):
                # 命中！我們手動一個字一個字轉，不透過 pypinyin
                for i, char in enumerate(word):
                    # 取出對應的注音 (如果使用者給的注音數量不夠，就 fallback 到空字串)
                    user_zhuyin = bopomofo_list[i] if i < len(bopomofo_list) else ""
                    
                    # 呼叫下方的「單字轉點字」核心邏輯
                    char_braille, is_err = convert_single_char_zhuyin(char, user_zhuyin, rules)
                    
                    full_braille += char_braille
                    dual_list.append({'char': char, 'braille': char_braille, 'is_error': is_err})
                
                text_index += len(word)
                is_number_mode = False
                match_bopomofo = True
                break
        if match_bopomofo: continue

        # --- 4. 標準處理流程 (沒命中規則) ---
        # 因為 pypinyin 可能把多個非中文字合在一起，我們需要對齊
        # 尋找目前 text_index 對應到 full_pinyin_list 的哪一個項目
        # 這部分邏輯較複雜，我們簡化處理：直接針對當前單字處理
        
        # 為了安全，我們這裡稍微退回一點：單字處理 (除非是非中文)
        # 這樣可以確保索引對齊
        
        char = text[text_index]
        
        # A. 非中文處理
        if not ('\u4e00' <= char <= '\u9fff'):
            char_braille = ""
            if char.isdigit():
                if not is_number_mode:
                    char_braille += rules.SPECIAL['NUMBER_PREFIX']
                    is_number_mode = True
                if char in SAFE_NUMBER_MAP:
                    char_braille += SAFE_NUMBER_MAP[char]
                elif char in rules.PUNCTUATION:
                        char_braille += rules.PUNCTUATION[char]
            elif char in rules.PUNCTUATION:
                is_number_mode = False
                char_braille += rules.PUNCTUATION[char]
            else:
                is_number_mode = False
                char_braille += char 
            
            full_braille += char_braille
            dual_list.append({'char': char, 'braille': char_braille, 'is_error': False})
            text_index += 1
            continue

        # B. 中文處理
        is_number_mode = False
        # 重新對這個字取注音 (因為 pypinyin 列表可能已經對不齊了，單字取最保險)
        # 注意：這裡會失去內建破音字功能，但因為我們有 default_polyphone_fixes，所以還好
        # 如果要保留整句破音字，需要更複雜的對齊，但在有「強制修正」功能下，單字取是可接受的妥協
        single_pinyin = pinyin(char, style=Style.BOPOMOFO)
        zhuyin = single_pinyin[0][0]
        
        char_braille, is_err = convert_single_char_zhuyin(char, zhuyin, rules)
        
        full_braille += char_braille
        dual_list.append({'char': char, 'braille': char_braille, 'is_error': is_err})
        text_index += 1

    return full_braille, dual_list

# --- 抽離出的核心轉譯函式 (讓標準流程和強制修正都能共用) ---
def convert_single_char_zhuyin(char, zhuyin, rules):
    sheng = ""
    yun = ""
    tone = ""
    is_error = False 
    
    temp_zhuyin = zhuyin
    
    # 1. 聲調
    if temp_zhuyin and temp_zhuyin[-1] in rules.TONES:
        tone = rules.TONES[temp_zhuyin[-1]]
        temp_zhuyin = temp_zhuyin[:-1] 
    elif '˙' in temp_zhuyin:
            tone = rules.TONES[5]
            temp_zhuyin = temp_zhuyin.replace('˙', '')
    else:
        tone = rules.TONES[1]

    # 2. 聲母
    for initial in rules.INITIALS:
        if temp_zhuyin.startswith(initial):
            sheng = rules.INITIALS[initial]
            temp_zhuyin = temp_zhuyin[len(initial):]
            break
    
    # 3. 韻母
    if temp_zhuyin in rules.COMBINED_FINALS:
        yun = rules.COMBINED_FINALS[temp_zhuyin]
    elif temp_zhuyin in rules.FINALS:
        yun = rules.FINALS[temp_zhuyin]
        
    # 4. 空韻母補救
    if sheng and not yun:
            # 這裡簡單判斷：如果聲母是特定族群，補ㄦ
            # 由於 temp_zhuyin 已經被切掉聲母，如果它空了，代表原本只有聲母
            if not temp_zhuyin: 
                # 反查聲母文字比較麻煩，直接看原始注音開頭
                if zhuyin[0] in rules.ZI_CHI_SHI_RI_GROUPS:
                    yun = rules.FINALS['ㄦ']
    
    if not yun:
        is_error = True
    
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