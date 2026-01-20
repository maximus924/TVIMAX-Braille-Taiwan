import streamlit as st
import braille_converter
import time

# --- 1. 頁面設定 ---
st.set_page_config(
    page_title="麥西家正體中文字點字即時轉譯小麥麥",
    layout="wide",
)

# --- 2. CSS 美化 ---
st.markdown("""
<style>
    .braille-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        line-height: 1.5;
    }
    .braille-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: 1px solid #ced4da;
        background-color: white;
        border-radius: 4px;
        padding: 4px;
        min-width: 32px;
        margin-bottom: 5px;
    }
    .error-box {
        border: 2px solid #ff4b4b !important;
        background-color: #ffe6e6 !important;
    }
    .char-top {
        font-size: 14px;
        color: #495057;
        margin-bottom: 2px;
        font-family: "Microsoft JhengHei", sans-serif;
    }
    .braille-bottom {
        font-weight: bold;
        color: #000;
    }
    .break-line {
        flex-basis: 100%;
        height: 0;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 設定與修正")
    
    status_placeholder = st.empty()
    status_placeholder.info("系統狀態：核心就緒 🟢")
    st.divider()

    st.subheader("📝 我的詞庫 (即時修正)")
    st.info("格式：詞彙=點字 或 注音 例如：\nBoyan = ⠃⠕⠽⠁⠝\n快樂 = ㄎㄨㄞˋ ㄌㄜˋ")
    
    default_dict = "Boyan=⠠⠃⠕⠽⠁⠝\n快樂=ㄎㄨㄞˋ ㄌㄜˋ\n冠軍=ㄍㄨㄢˋ ㄐㄩㄣ"
    custom_dict_str = st.text_area("在此輸入自定義規則", value=default_dict, height=150)
    
    custom_rules = {}
    if custom_dict_str:
        for line in custom_dict_str.split('\n'):
            if '=' in line:
                k, v = line.split('=', 1)
                custom_rules[k.strip()] = v.strip()

    st.divider()
    
    # [新增] 英文標準切換
    st.subheader("🔠 英文點字標準")
    english_mode_option = st.radio(
        "請選擇轉譯模式：",
        ["UEB (統一英文點字)", "Traditional (傳統/舊版點字)"],
        index=0,
        help="UEB：括號使用 ⠐⠣ ⠐⠜，全大寫使用雙點。\n傳統：括號使用 ⠪ ⠕，大寫規則較簡單。"
    )
    # 將中文選項轉換為程式碼代號
    english_mode = "UEB" if "UEB" in english_mode_option else "Traditional"

    st.subheader("📄 排版設定")
    chars_per_line = st.number_input("每行方數", min_value=10, max_value=60, value=32)
    font_size_px = st.slider("字體大小", 12, 36, 22)

# --- 4. 主畫面 ---
st.title("麥西家正體中文字點字即時轉譯小麥麥")
st.markdown("支援：全形轉半形、英文大小寫、即時破音字修正、雙重格式匯出")

st.header("輸入文字")
input_text = st.text_area("請在此貼上文章...", height=150, placeholder="例如：Boyan (WHIP: 1.20)...")

if input_text:
    # 傳入 english_mode
    full_result, dual_data = braille_converter.text_to_braille(input_text, custom_rules, english_mode)
    
    st.subheader("點字輸出 ⠒")
    st.text_area("純點字", value=full_result, height=150)
    
    c1, c2 = st.columns([1, 1])
    with c1:
        st.download_button("📥 下載 .txt (印表機用)", full_result, "braille_output.txt")
    
    html_content = braille_converter.generate_html_content(dual_data, chars_per_line, font_size_px)
    
    full_html_file = f"""
    <html>
    <head><meta charset="utf-8"><style>
    .braille-container {{ display: flex; flex-wrap: wrap; gap: 5px; }}
    .braille-box {{ border: 1px solid #ccc; padding: 5px; margin: 2px; text-align: center; }}
    .braille-bottom {{ font-size: {font_size_px}px; font-weight: bold; }}
    .break-line {{ flex-basis: 100%; height: 0; }}
    </style></head>
    <body>
    <h2>雙視對照表</h2>
    {html_content}
    </body></html>
    """
    
    with c2:
        st.download_button("🌏 下載 .html (雙視對照)", full_html_file, "dual_view.html", mime="text/html")

    st.divider()
    st.header("雙視校對區")
    st.markdown(html_content, unsafe_allow_html=True)