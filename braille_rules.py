# 檔案名稱: braille_rules.py (v16 Nemeth 數學升級版)

# 1. 聲母 (Initials) - 中文不變
INITIALS = {
    'ㄅ': '⠕', 'ㄆ': '⠏', 'ㄇ': '⠍', 'ㄈ': '⠟',
    'ㄉ': '⠙', 'ㄊ': '⠋', 'ㄋ': '⠝', 'ㄌ': '⠉',
    'ㄍ': '⠅', 'ㄎ': '⠇', 'ㄏ': '⠗',
    'ㄐ': '⠅', 'ㄑ': '⠚', 'ㄒ': '⠑',
    'ㄓ': '⠁', 'ㄔ': '⠃', 'ㄕ': '⠊', 'ㄖ': '⠛',
    'ㄗ': '⠓', 'ㄘ': '⠚', 'ㄙ': '⠑'
}

ZI_CHI_SHI_RI_GROUPS = {'ㄓ', 'ㄔ', 'ㄕ', 'ㄖ', 'ㄗ', 'ㄘ', 'ㄙ'}

# 2. 韻母 (Finals) - 中文不變
FINALS = {
    'ㄚ': '⠜', 'ㄛ': '⠣', 'ㄜ': '⠮', 'ㄝ': '⠢',
    'ㄞ': '⠺', 'ㄟ': '⠴', 'ㄠ': '⠩', 'ㄡ': '⠷',
    'ㄢ': '⠧', 'ㄣ': '⠥', 'ㄤ': '⠭', 'ㄥ': '⠵',
    'ㄦ': '⠱', 'ㄧ': '⠡', 'ㄨ': '⠌', 'ㄩ': '⠳'
}

# 3. 結合韻 (Combined Finals) - 中文不變
COMBINED_FINALS = {
    'ㄧㄚ': '⠾', 'ㄨㄚ': '⠔', 'ㄧㄛ': '⠴', 'ㄨㄛ': '⠒',
    'ㄧㄝ': '⠬', 'ㄩㄝ': '⠦', 'ㄧㄞ': '⠢', 'ㄨㄞ': '⠶',
    'ㄨㄟ': '⠫', 'ㄧㄠ': '⠪', 'ㄧㄡ': '⠎', 'ㄧㄢ': '⠞',
    'ㄨㄢ': '⠻', 'ㄩㄢ': '⠘', 'ㄧㄣ': '⠹', 'ㄨㄣ': '⠿',
    'ㄩㄣ': '⠲', 'ㄧㄤ': '⠨', 'ㄨㄤ': '⠸', 'ㄧㄥ': '⠽',
    'ㄨㄥ': '⠯', 'ㄩㄥ': '⠖'
}

# 4. 聲調 (Tones) - 中文不變
TONES = {
    1: '⠄', 'ˊ': '⠂', 'ˇ': '⠈', 'ˋ': '⠐', '˙': '⠁', 5: '⠁'
}

# 5. 標點符號 (Punctuation) - 一般文字模式用
PUNCTUATION_BASE = {
    '，': '⠆', ',': '⠆', '、': '⠠', '；': '⠰', ';': '⠰',
    '：': '⠒⠒', ':': '⠒⠒', '。': '⠤', '.': '⠤',
    '？': '⠕', '?': '⠕', '！': '⠇', '!': '⠇',
    '「': '⠰⠤', '」': '⠤⠆', '【': '⠯', ']': '⠽',
    '『': '⠰⠤', '』': '⠤⠆', '—': '⠒⠒', '-': '⠒',
    '（': '⠪', '）': '⠕'
}

# 舊版英文/傳統
PUNCTUATION_TRADITIONAL = PUNCTUATION_BASE.copy()
PUNCTUATION_TRADITIONAL.update({
    '(': '⠪', ')': '⠕', '[': '⠯', ']': '⠽'
})

# 新版英文 (UEB)
PUNCTUATION_UEB = PUNCTUATION_BASE.copy()
PUNCTUATION_UEB.update({
    '(': '⠐⠣', ')': '⠐⠜', '[': '⠨⠣', ']': '⠨⠜'
})

# 6. 特殊符號 (一般文字模式)
SPECIAL_TRADITIONAL = {
    'NUMBER_PREFIX': '⠼', 'CAP_SYMBOL': '⠠', 'WORD_CAP_SYMBOL': '⠠⠠', 'SPACE': '  '
}
SPECIAL_UEB = {
    'NUMBER_PREFIX': '⠼', 'CAP_SYMBOL': '⠠', 'WORD_CAP_SYMBOL': '⠠⠠', 'SPACE': '  '
}

# 7. 英文字母 (共用)
ENGLISH = {
    'a': '⠁', 'b': '⠃', 'c': '⠉', 'd': '⠙', 'e': '⠑',
    'f': '⠋', 'g': '⠛', 'h': '⠓', 'i': '⠊', 'j': '⠚',
    'k': '⠅', 'l': '⠇', 'm': '⠍', 'n': '⠝', 'o': '⠕',
    'p': '⠏', 'q': '⠟', 'r': '⠗', 's': '⠎', 't': '⠞',
    'u': '⠥', 'v': '⠧', 'w': '⠺', 'x': '⠭', 'y': '⠽', 'z': '⠵'
}

# === [新增] 8. 聶美茲數學符號庫 (Nemeth Code) ===
NEMETH = {
    # 數字 (Dropped Numbers: 下位點)
    'DIGITS': {
        '1': '⠂', '2': '⠆', '3': '⠒', '4': '⠲', '5': '⠢',
        '6': '⠖', '7': '⠶', '8': '⠦', '9': '⠔', '0': '⠴'
    },
    
    # 運算符號
    'OPERATORS': {
        '+': '⠬',  # Plus (dots 3-4-6)
        '-': '⠤',  # Minus (dots 3-6)
        '×': '⠈⠡', # Multiplication Cross (dots 4, 1-6)
        '*': '⠈⠡', # 通用乘號對應
        '÷': '⠨⠌', # Division (dots 4-6, 3-4)
        '/': '⠨⠌', # 通用除號對應
        '=': '⠀⠨⠅⠀', # Equals (Space, dots 4-6, 1-3, Space) 注意前後空格
        '>': '⠀⠨⠂⠀', # Greater than (Space, dots 4-6, 2, Space)
        '<': '⠀⠐⠅⠀', # Less than (Space, dots 5, 1-3, Space)
        '.': '⠨',  # Decimal point (dot 4-6)
        ',': '⠠',  # Comma (dot 6)
    },
    
    # 分數與上下標
    'INDICATORS': {
        'NUMERIC': '⠼',      # Numeric Indicator (dots 3-4-5-6)
        'FRACTION_OPEN': '⠹', # Simple Fraction Open (dots 1-4-5-6)
        'FRACTION_CLOSE': '⠼',# Simple Fraction Close (dots 3-4-5-6)
        'FRACTION_LINE': '⠌', # Fraction Line (dots 3-4)
        'SUPERSCRIPT': '⠘',   # Superscript/Exponent (dots 4-5)
        'SUBSCRIPT': '⠰',     # Subscript (dots 5-6)
        'SPACE': ' '           # Nemeth context space
    },
    
    # 括號
    'PARENTHESES': {
        '(': '⠷', # Open Parenthesis (dots 1-2-3-5-6)
        ')': '⠾', # Close Parenthesis (dots 2-3-4-5-6)
        '[': '⠨⠷',
        ']': '⠨⠾',
        '{': '⠸⠷',
        '}': '⠸⠾'
    },

    # 模式切換指標
    'SWITCH': {
        'START': '⠸⠩⠀', # Begin Nemeth Code (dots 4-5-6, 1-4-6, space)
        'END': '⠀⠸⠱'    # End Nemeth Code (space, dots 4-5-6, 1-5-6)
    }
}