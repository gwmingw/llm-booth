print("AI 문장 이어가기 부스 데모를 실행합니다.")

import torch
import os
import textwrap
import tkinter as tk
from tkinter import font as tkfont
import unicodedata
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.ft2font import FT2Font
from matplotlib.widgets import Button
from wordcloud import WordCloud
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, QuantoConfig
except ImportError as error:
    raise ImportError(
        "transformers와 huggingface-hub 버전 조합이 맞지 않습니다. "
        "ui_wordcloud_booth_tkinput 폴더에서 새 가상환경을 만들고 "
        "`pip install -r requirements.txt`를 실행한 뒤 다시 시작해 주세요."
    ) from error

# 모델과 토크나이저 불러오기
model_name = "Qwen/Qwen2.5-1.5B-Instruct"
print("AI 모델을 준비하고 있습니다. 잠시만 기다려 주세요...")

tokenizer = AutoTokenizer.from_pretrained(model_name)
quant_config = QuantoConfig(weights="int8") # 8비트(INT8) 양자화 설정 객체 생성

# 모델 로드 시 양자화 설정을 주입하여 압축된 상태로 메모리에 올림
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=quant_config,
    device_map="auto"
)

def ask_start_prompt(parent=None, initial_text=""):
    result = {"text": None}

    owns_root = parent is None
    root = tk.Tk() if owns_root else tk.Toplevel(parent)
    root.title("시작 문장 입력")
    root.configure(bg="#f6f8fb")
    root.resizable(False, False)
    root.attributes("-topmost", True)
    if parent is not None:
        root.transient(parent)
        root.grab_set()

    ui_font = tkfont.Font(family="Noto Sans KR", size=13)
    entry_font = tkfont.Font(family="Noto Sans KR", size=20)
    title_font = tkfont.Font(family="Noto Sans KR", size=15, weight="bold")

    frame = tk.Frame(root, bg="#f6f8fb", padx=30, pady=24)
    frame.pack(fill="both", expand=True)

    tk.Label(
        frame,
        text="시작 문장을 입력해 주세요",
        bg="#f6f8fb",
        fg="#18324a",
        font=title_font
    ).pack(anchor="w")
    tk.Label(
        frame,
        text="예: 오늘 학교에 갔는데",
        bg="#f6f8fb",
        fg="#5d6b7a",
        font=ui_font
    ).pack(anchor="w", pady=(6, 12))

    entry = tk.Entry(frame, width=31, font=entry_font, relief="solid", bd=1)
    entry.pack(fill="x", ipady=11)
    entry.insert(0, initial_text)

    button_row = tk.Frame(frame, bg="#f6f8fb")
    button_row.pack(fill="x", pady=(16, 0))

    def submit():
        text = entry.get().strip()
        if text:
            result["text"] = text
            root.destroy()

    def close_without_start():
        result["text"] = None
        root.destroy()

    start_button = tk.Button(
        button_row,
        text="시작하기",
        command=submit,
        font=ui_font,
        bg="#dbeaf5",
        fg="#18324a",
        activebackground="#c8dfef",
        relief="flat",
        padx=18,
        pady=8
    )
    start_button.pack(side="right")

    root.bind("<Return>", lambda _event: submit())
    root.protocol("WM_DELETE_WINDOW", close_without_start)
    root.update_idletasks()

    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() - width) // 2
    y = (root.winfo_screenheight() - height) // 3
    root.geometry(f"{width}x{height}+{x}+{y}")

    entry.focus_set()
    root.lift()
    if owns_root:
        root.mainloop()
    else:
        parent.wait_window(root)
    return result["text"]


# 워드클라우드 생성 함수 정의
def run_wordcloud(model, tokenizer, top_n=30):
    # 한글 폰트 설정
    font_candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%/Microsoft/Windows/Fonts/NanumSquareRoundB.ttf"),
        os.path.expandvars(r"%LOCALAPPDATA%/Microsoft/Windows/Fonts/NanumSquareRoundR.ttf"),
        "c:/Windows/Fonts/NotoSansKR-Regular.ttf",
        "c:/Windows/Fonts/NotoSansKR-Medium.ttf",
        "c:/Windows/Fonts/malgun.ttf",
        "/System/Library/Fonts/AppleGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    ]
    bold_font_candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%/Microsoft/Windows/Fonts/NanumSquareRoundEB.ttf"),
        os.path.expandvars(r"%LOCALAPPDATA%/Microsoft/Windows/Fonts/NanumSquareRoundB.ttf"),
        "c:/Windows/Fonts/NotoSansKR-Bold.ttf",
        "c:/Windows/Fonts/NotoSansKR-Medium.ttf",
        "c:/Windows/Fonts/malgunbd.ttf",
    ]
    font_path = next((path for path in font_candidates if os.path.exists(path)), font_candidates[0])
    bold_font_path = next((path for path in bold_font_candidates if os.path.exists(path)), font_path)
    font_prop = FontProperties(fname=font_path)
    bold_font_prop = FontProperties(fname=bold_font_path)
    font_face = FT2Font(font_path)

    # 화면 분할
    fig, (ax_text, ax_wc) = plt.subplots(
        2,
        1,
        figsize=(13.5, 8.5),
        gridspec_kw={'height_ratios': [1.45, 4], 'hspace': 0.18}
    )
    fig.canvas.manager.set_window_title('AI 문장 이어가기 부스')
    fig.patch.set_facecolor("#f6f8fb")
    
    # 모델을 감성적으로 만드는 숨겨진 프롬프트
    hidden_prefix = (
        "[당신은 감수성이 풍부하고 세상을 아름답게 바라보는 시인입니다. "
        "서정적이고 감동적인 시어로 다음 문장을 이어가세요.]\n\n"
    )
    
    state = {"text": ""}

    def probability_color(prob, min_prob, max_prob):
        # 낮은 확률은 차분한 청록, 높은 확률은 부드러운 코랄로 보여준다.
        if max_prob <= min_prob:
            ratio = 1.0
        else:
            ratio = (prob - min_prob) / (max_prob - min_prob)

        palette = [
            (49, 130, 148),   # teal
            (73, 104, 172),   # soft blue
            (122, 92, 181),   # gentle violet
            (210, 105, 124),  # muted coral
        ]
        segment_count = len(palette) - 1
        scaled = ratio * segment_count
        index = min(int(scaled), segment_count - 1)
        local_ratio = scaled - index
        start = palette[index]
        end = palette[index + 1]
        rgb = tuple(int(start[i] + (end[i] - start[i]) * local_ratio) for i in range(3))
        return tuple(value / 255.0 for value in rgb)

    def is_booth_safe_text(text):
        for char in text:
            if char.isspace():
                continue

            codepoint = ord(char)
            category = unicodedata.category(char)

            if char == "\ufffd" or category[0] == "C":
                return False
            if 0x4E00 <= codepoint <= 0x9FFF:
                return False
            if 0x3400 <= codepoint <= 0x4DBF:
                return False
            if 0xF900 <= codepoint <= 0xFAFF:
                return False
            if 0x3040 <= codepoint <= 0x30FF:
                return False
            if codepoint >= 0x1F000:
                return False
            if font_face.get_char_index(codepoint) == 0:
                return False

        return True

    def draw_current_state():
        # [상단 영역] 완성된 문장 표시 (숨겨진 프롬프트는 보여주지 않음)
        ax_text.clear()
        ax_text.axis('off')
        ax_text.set_facecolor("#f6f8fb")
        
        wrapped_text = textwrap.fill(state["text"], width=64)
        sentence_font_size = 18 if len(state["text"]) < 90 else 15
        panel_style = dict(boxstyle="round,pad=0.8", facecolor="#ffffff", edgecolor="#7f9fbe", linewidth=2.4)
        
        ax_text.text(
            0.02,
            0.92,
            "AI가 다음 말을 예측하고 있어요",
            ha='left',
            va='top',
            fontsize=19,
            color="#18324a",
            fontproperties=bold_font_prop,
            transform=ax_text.transAxes
        )
        ax_text.text(
            0.02,
            0.66,
            "아래 말들 중 하나를 클릭해 문장을 이어 보세요. 글자가 클수록 다음에 올 가능성이 높아요.",
            ha='left',
            va='top',
            fontsize=12.5,
            color="#32495f",
            fontproperties=font_prop,
            transform=ax_text.transAxes
        )
        ax_text.text(
            0.5,
            0.26,
            wrapped_text,
            ha='center',
            va='center',
            fontsize=sentence_font_size,
            color="#17202a",
            fontproperties=font_prop,
            bbox=panel_style,
            linespacing=1.45,
            transform=ax_text.transAxes
        )

        # [하단 영역] 워드클라우드 표시
        cloud_width = 980
        cloud_height = 510
        ax_wc.clear()
        ax_wc.axis('off')
        ax_wc.set_xlim(0, cloud_width)
        ax_wc.set_ylim(cloud_height + 18, -8)
        ax_wc.set_facecolor("#ffffff")
        
        # 모델에 숨겨진 지시문과 현재 문장을 합쳐서 전달
        full_text_for_model = hidden_prefix + state["text"]
        
        inputs = tokenizer(full_text_for_model, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model(**inputs)
        
        logits = outputs.logits[0, -1, :]
        probs = torch.nn.functional.softmax(logits, dim=-1)
        search_n = min(top_n * 4, probs.shape[-1])
        top_probs, top_indices = torch.topk(probs, search_n)
        
        token_data = {}
        for i in range(search_n):
            token_id = top_indices[i].item()
            prob = top_probs[i].item()
            
            # 특수 토큰(BOS, EOS 등)을 제외하고 디코딩
            raw_str = tokenizer.decode([token_id], skip_special_tokens=True)
            display_str = raw_str.strip()
            
            # 공백, 빈 문자열이 포함된 경우 스킵
            if not display_str:
                continue
            if not is_booth_safe_text(display_str):
                continue
                
            if display_str not in token_data:
                token_data[display_str] = {"prob": prob, "raw": raw_str}
            else:
                token_data[display_str]["prob"] += prob

            if len(token_data) >= top_n:
                break
                
        freqs = {k: v["prob"] for k, v in token_data.items()}
        
        # 상위 토큰이 모두 필터링되어 freqs가 비었을 경우의 방어 로직
        if not freqs:
            fallback_text = "[더 이상 예측할 단어가 없습니다]"
            freqs = {fallback_text: 1.0}
            token_data[fallback_text] = {"prob": 1.0, "raw": ""}

        min_prob = min(freqs.values())
        max_prob = max(freqs.values())
        
        # 워드클라우드 생성
        wc = WordCloud(
            font_path=font_path,
            width=cloud_width,
            height=cloud_height,
            background_color='white',
            max_font_size=166,
            min_font_size=28,
            prefer_horizontal=1.0,
            relative_scaling=0.82,
            margin=10,
            random_state=12
        )
        wc.generate_from_frequencies(freqs)

        for item in wc.layout_:
            (word, freq), font_size, (y, x), orientation, _ = item
            rot_deg = 90 if orientation else 0
            mpl_color = probability_color(token_data[word]["prob"], min_prob, max_prob)
            display_font_size = max(19, font_size * 72 / fig.dpi * 1.54)
            
            # WordCloud의 픽셀 기준 글자 크기를 Matplotlib의 포인트 기준으로 변환한다.
            t = ax_wc.text(x, y, word, fontsize=display_font_size, color=mpl_color,
                           fontproperties=font_prop, rotation=rot_deg,
                           ha='left', va='top', picker=True)
            t.raw_str = token_data[word]["raw"]
            
        fig.canvas.draw()

    def draw_waiting_state(message=None):
        ax_text.clear()
        ax_text.axis('off')
        ax_text.set_facecolor("#f6f8fb")
        ax_text.text(
            0.02,
            0.82,
            "AI가 다음 말을 예측하고 있어요",
            ha='left',
            va='top',
            fontsize=19,
            color="#18324a",
            fontproperties=bold_font_prop,
            transform=ax_text.transAxes
        )
        ax_text.text(
            0.02,
            0.56,
            "잠시 후 입력창에 시작 문장을 적어 주세요.",
            ha='left',
            va='top',
            fontsize=12.5,
            color="#32495f",
            fontproperties=font_prop,
            transform=ax_text.transAxes
        )

        ax_wc.clear()
        ax_wc.axis('off')
        ax_wc.set_facecolor("#ffffff")
        if message:
            ax_wc.text(
                0.5,
                0.52,
                message,
                ha='center',
                va='center',
                fontsize=28,
                color="#7f9fbe",
                fontproperties=bold_font_prop,
                transform=ax_wc.transAxes
            )
        fig.canvas.draw_idle()

    def request_new_prompt(_=None):
        draw_waiting_state()
        prompt = ask_start_prompt(parent=fig.canvas.manager.window)
        if not prompt:
            draw_waiting_state("처음부터 버튼을 눌러 시작 문장을 입력해 주세요")
            return

        state["text"] = prompt
        draw_current_state()

    # 클릭 이벤트 처리
    def on_pick(event):
        text_obj = event.artist
        if hasattr(text_obj, 'raw_str'):
            selected_token = text_obj.raw_str
            # 빈 문자열 클릭 시 무시
            if not selected_token:
                return
                
            state["text"] += selected_token
            draw_current_state()

    fig.canvas.mpl_connect('pick_event', on_pick)

    reset_ax = fig.add_axes([0.82, 0.025, 0.12, 0.052])
    reset_button = Button(reset_ax, "처음부터", color="#f5e8eb", hovercolor="#edd6dc")
    reset_button.label.set_fontproperties(font_prop)
    reset_button.label.set_fontweight("bold")
    reset_button.label.set_color("#5f2d3a")
    reset_button.on_clicked(request_new_prompt)
    
    plt.subplots_adjust(left=0.055, right=0.945, top=0.95, bottom=0.11)
    draw_waiting_state()
    fig.canvas.draw_idle()
    fig.canvas.manager.window.after(200, request_new_prompt)
    plt.show()

# 함수 실행
run_wordcloud(model=model, tokenizer=tokenizer, top_n=30)
