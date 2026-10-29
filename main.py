import flet as ft
import edge_tts
import asyncio
import re
import os
import shutil
import json
import time
import base64
from datetime import datetime

# ==========================================
# PLATINUM VOICE - WEBVIEW AUDIO PLAYER
# ==========================================

GRADIENT_COLORS = ["#1A0B2E", "#2D1B4E", "#0F2027", "#203A43"] 
COLOR_GOLD = "#FFD700"
COLOR_TEXT = "#FFFFFF"
COLOR_TEXT_MUTED = "#B0BEC5"
COLOR_ERROR = "#FF5252"

GLASS_BG = "#22FFFFFF" 
GLASS_BORDER = "#44FFFFFF" 
GLASS_INPUT_BG = "#11000000" 

VOICE_PROFILES = {
    "🇲🇲 နီလာ (မြန်မာ - မိန်းကလေး)": "my-MM-NilarNeural",
    "🇲🇲 သီဟ (မြန်မာ - ယောက်ျားလေး)": "my-MM-ThihaNeural",
    "🇺🇸 အယ်ရီယာ (အမေရိကန် - မိန်းကလေး)": "en-US-AriaNeural",
    "🇺🇸 ဂိုင်း (အမေရိကန် - ယောက်ျားလေး)": "en-US-GuyNeural",
    "🇺🇸 ဂျယ်နီ (အမေရိကန် - မိန်းကလေး)": "en-US-JennyNeural",
    "🇬🇧 ဆိုနီယာ (ဗြိတိန် - မိန်းကလေး)": "en-GB-SoniaNeural",
    "🇬🇧 ရိုင်ယန် (ဗြိတိန် - ယောက်ျားလေး)": "en-GB-RyanNeural",
    "🇯🇵 နာနာမိ (ဂျပန် - မိန်းကလေး)": "ja-JP-NanamiNeural",
    "🇯🇵 ကေးတာ (ဂျပန် - ယောက်ျားလေး)": "ja-JP-KeitaNeural",
    "🇹🇭 ပရီဝါဒီ (ထိုင်း - မိန်းကလေး)": "th-TH-PremwadeeNeural",
    "🇹🇭 နီဝတ် (ထိုင်း - ယောက်ျားလေး)": "th-TH-NiwatNeural",
    "🇨🇳 ရှောရှောင် (တရုတ် - မိန်းကလေး)": "zh-CN-XiaoxiaoNeural",
    "🇨🇳 ယွန်ရှီ (တရုတ် - ယောက်ျားလေး)": "zh-CN-YunxiNeural",
    "🇰🇷 ဆန်းဟီ (ကိုရီးယား - မိန်းကလေး)": "ko-KR-SunHiNeural",
    "🇰🇷 အင်ဂျွန် (ကိုရီးယား - ယောက်ျားလေး)": "ko-KR-InJoonNeural",
    "🇫🇷 ဒင်နစ် (ပြင်သစ် - မိန်းကလေး)": "fr-FR-DeniseNeural",
    "🇩🇪 ကာတရင် (ဂျာမန် - မိန်းကလေး)": "de-DE-KatjaNeural",
    "🇪🇸 အယ်လ်ဗာ (စပိန် - မိန်းကလေး)": "es-ES-ElviraNeural",
}

def split_unlimited_text(text: str, max_chunk_size: int = 2000) -> list[str]:
    if not text or not text.strip(): return []
    paragraphs = re.split(r'\n\s*\n', text.strip())
    chunks, current_chunk = [], ""
    for para in paragraphs:
        para = para.strip()
        if not para: continue
        if len(para) > max_chunk_size:
            sentences = re.split(r'(?<=[။!?])\s*', para)
            for sent in sentences:
                sent = sent.strip()
                if not sent: continue
                if len(current_chunk) + len(sent) + 1 <= max_chunk_size:
                    current_chunk += (" " if current_chunk else "") + sent
                else:
                    if current_chunk: chunks.append(current_chunk)
                    if len(sent) > max_chunk_size:
                        words = sent.split(' ')
                        temp = ""
                        for w in words:
                            if len(temp) + len(w) + 1 <= max_chunk_size:
                                temp += (" " if temp else "") + w
                            else:
                                if temp: chunks.append(temp)
                                temp = w
                        if temp: current_chunk = temp
                    else: current_chunk = sent
        else:
            if len(current_chunk) + len(para) + 2 <= max_chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                if current_chunk: chunks.append(current_chunk)
                current_chunk = para
    if current_chunk: chunks.append(current_chunk)
    return [c for c in chunks if c.strip()]

def merge_audio_files(file_paths: list[str], output_path: str) -> bool:
    try:
        with open(output_path, 'wb') as outfile:
            for path in file_paths:
                if os.path.exists(path):
                    with open(path, 'rb') as infile:
                        outfile.write(infile.read())
        return True
    except Exception as e:
        print(f"Merge Error: {e}")
        return False

def main(page: ft.Page):
    page.title = "Platinum Voice"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = ft.ScrollMode.HIDDEN 
    
    page.fonts = {
        "Padauk": "https://github.com/google/fonts/raw/main/ofl/padauk/Padauk-Regular.ttf"
    }
    page.theme = ft.Theme(font_family="Padauk")

    page.bgcolor = ft.LinearGradient(
        begin=ft.Alignment.TOP_LEFT,
        end=ft.Alignment.BOTTOM_RIGHT,
        colors=GRADIENT_COLORS,
    )

    splash_view = ft.Container(
        content=ft.Column(
            [
                ft.Image(src="logo.png", width=150, height=150),
                ft.Container(height=20),
                ft.Text("PLATINUM VOICE", size=32, weight=ft.FontWeight.BOLD, color=COLOR_GOLD),
                ft.Text("MULTI-LANGUAGE TTS", size=14, color=COLOR_TEXT_MUTED),
                ft.Container(height=50),
                ft.ProgressRing(color=COLOR_GOLD, width=40, height=40, stroke_width=4),
                ft.Container(height=100),
                ft.Text("Developed By Dexter Syntax", size=12, color=COLOR_TEXT_MUTED, italic=True),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.Alignment.CENTER,
        expand=True,
    )
    
    page.add(splash_view)

    async def load_main_app():
        await asyncio.sleep(2.5)
        page.clean()
        setup_main_ui(page)

    page.run_task(load_main_app)


def setup_main_ui(page: ft.Page):
    is_generating = False
    is_previewing = False
    prefs = ft.SharedPreferences()

    async def load_data_async():
        try:
            presets_str = await prefs.get("my_presets")
            pronun_str = await prefs.get("my_pronunciations")
            
            p_data = json.loads(presets_str) if presets_str else {}
            pr_data = json.loads(pronun_str) if pronun_str else {}
            return p_data, pr_data
        except:
            return {}, {}

    presets_data = {}
    pronunciations_data = {}

    def load_data():
        nonlocal presets_data, pronunciations_data
        future = page.run_task(load_data_async)
        def on_done(f):
            nonlocal presets_data, pronunciations_data
            try:
                p, pr = f.result()
                presets_data = p
                pronunciations_data = pr
                update_presets_ui()
            except Exception:
                pass
        future.add_done_callback(on_done)

    def save_presets_to_storage(presets_dict):
        async def _save():
            await prefs.set("my_presets", json.dumps(presets_dict))
        page.run_task(_save)

    def save_pronuns_to_storage(pronun_dict):
        async def _save():
            await prefs.set("my_pronunciations", json.dumps(pronun_dict))
        page.run_task(_save)

    def glass_card(content, padding=20):
        return ft.Container(
            content=content,
            bgcolor=GLASS_BG,
            padding=padding,
            border_radius=24,
            border=ft.Border.all(1, GLASS_BORDER),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color="#30000000",
                offset=ft.Offset(0, 10),
            ),
        )

    def close_dlg(dlg):
        dlg.open = False
        page.update()

    def show_qr(e):
        dlg = ft.AlertDialog(
            title=ft.Text("မုန့်ဖိုးပေးရန်", color=COLOR_GOLD, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                [
                    ft.Text("KBZ Pay", size=22, weight=ft.FontWeight.W_900, color=COLOR_TEXT),
                    ft.Container(height=10),
                    ft.Image(src="kpay_qr.jpg", width=250, height=250, fit=ft.BoxFit.CONTAIN),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
                tight=True,
            ),
            actions=[ft.TextButton("ပိတ်မည်", on_click=lambda e: close_dlg(dlg))],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            bgcolor="#2D1B4E", 
            shape=ft.RoundedRectangleBorder(radius=20),
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def show_pronun_dialog(e):
        word_input = ft.TextField(hint_text="မူရက်စာလုံး (ဥပမာ - AI)", bgcolor=GLASS_INPUT_BG, color=COLOR_TEXT, text_size=14, width=280)
        replace_input = ft.TextField(hint_text="အစားထိုးမည့် အသံထွက် (ဥပမာ - အေ-အိုင်)", bgcolor=GLASS_INPUT_BG, color=COLOR_TEXT, text_size=14, width=280)
        list_container = ft.Column(spacing=10)

        def update_list():
            list_container.controls.clear()
            if not pronunciations_data:
                list_container.controls.append(ft.Text("ပြင်ဆင်ထားသော စာလုံး မရှိပါ။", size=12, color=COLOR_TEXT_MUTED, italic=True))
            else:
                for k, v in pronunciations_data.items():
                    def make_del(key=k):
                        return lambda e: delete_pronun(key)
                    list_container.controls.append(
                        ft.Row([
                            ft.Text(f"{k} ➔ {v}", color=COLOR_GOLD, expand=True, size=13),
                            ft.IconButton(ft.Icons.DELETE, icon_color=COLOR_ERROR, icon_size=18, on_click=make_del())
                        ])
                    )
            page.update()

        def add_pronun(e):
            w = word_input.value.strip()
            r = replace_input.value.strip()
            if w and r:
                pronunciations_data[w] = r
                save_pronuns_to_storage(pronunciations_data)
                word_input.value = ""
                replace_input.value = ""
                update_list()

        def delete_pronun(key):
            if key in pronunciations_data:
                del pronunciations_data[key]
                save_pronuns_to_storage(pronunciations_data)
                update_list()

        add_btn = ft.Button("ထည့်မည်", bgcolor=COLOR_GOLD, color="#000000", on_click=add_pronun)

        update_list()

        dlg = ft.AlertDialog(
            title=ft.Text("အသံထွက် ပြင်ဆင်ရန်", color=COLOR_GOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("မြန်မာစာသားထဲမှာ အင်္ဂလိပ်စာလုံးတွေ ပါလာရင် အသံထွက်မှားတတ်ပါတယ်။ ဒီနေရာမှာ ကိုယ်လိုချင်တဲ့ အသံထွက်နဲ့ လဲလှယ်ထားနိုင်ပါတယ်။", size=12, color=COLOR_TEXT_MUTED),
                    word_input,
                    replace_input,
                    ft.Row([add_btn], alignment=ft.MainAxisAlignment.END),
                    ft.Divider(color=GLASS_BORDER),
                    ft.Text("ပြင်ဆင်ထားသော စာလုံးများ", size=14, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                    list_container
                ], spacing=15, tight=True),
                width=300,
            ),
            actions=[ft.TextButton("ပိတ်မည်", on_click=lambda e: close_dlg(dlg))],
            bgcolor="#2D1B4E",
            shape=ft.RoundedRectangleBorder(radius=20),
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    header = ft.Row(
        [
            ft.Column(
                [
                    ft.Text("PLATINUM VOICE", size=26, weight=ft.FontWeight.W_900, color=COLOR_TEXT),
                    ft.Text("MULTI-LANGUAGE TTS", size=12, weight=ft.FontWeight.BOLD, color=COLOR_GOLD),
                ],
                spacing=2,
            ),
            ft.Container(
                content=ft.Text("PRO", size=12, weight=ft.FontWeight.BOLD, color="#000000"),
                bgcolor=COLOR_GOLD,
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                border_radius=8,
                shadow=ft.BoxShadow(blur_radius=15, color=COLOR_GOLD, offset=ft.Offset(0, 0)),
            )
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    text_input = ft.TextField(
        multiline=True,
        min_lines=8,
        max_lines=15,
        hint_text="သင့်စာသားကို ဒီနေရာမှာ ရိုက်ထည့်ပါ...",
        bgcolor=GLASS_INPUT_BG,
        border_color="transparent",
        color=COLOR_TEXT,
        cursor_color=COLOR_GOLD,
        text_size=16,
        content_padding=20,
        border_radius=16,
        on_change=lambda e: update_char_count(),
    )

    char_count_text = ft.Text("0 characters", size=12, color=COLOR_TEXT_MUTED)

    def clear_text(e):
        text_input.value = ""
        char_count_text.value = "0 characters"
        page.update()

    def update_char_count():
        count = len(text_input.value) if text_input.value else 0
        char_count_text.value = f"{count} characters"
        page.update()

    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    async def import_file(e):
        try:
            files = await file_picker.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["txt"]
            )
            if files and len(files) > 0:
                filepath = files[0].path
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                text_input.value = content
                update_char_count()
                status_text.value = "ဖိုင်ကို ဖတ်ယူပြီးပါပြီ။"
                page.update()
        except Exception as ex:
            status_text.value = f"ဖိုင်ဖတ်မရပါ: {str(ex)}"
            page.update()

    def clean_text(e):
        text = text_input.value
        if not text:
            status_text.value = "စာသားမရှိပါ။"
            page.update()
            return
        
        cleaned = text.replace('\r\n', '\n')
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        cleaned = cleaned.strip()
        
        text_input.value = cleaned
        update_char_count()
        status_text.value = "စာသားများကို သန့်ရှင်းရေးလုပ်ပြီးပါပြီ။"
        text_input.update()
        page.update()

    editor_card = glass_card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.EDIT_NOTE, color=COLOR_GOLD, size=22),
                        ft.Text("SCRIPT EDITOR", size=14, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                        ft.Row([
                            ft.IconButton(ft.Icons.FOLDER_OPEN, icon_color=COLOR_GOLD, icon_size=22, tooltip="Import .txt File", on_click=import_file),
                            ft.IconButton(ft.Icons.CLEANING_SERVICES, icon_color=COLOR_GOLD, icon_size=22, tooltip="Clean Text", on_click=clean_text),
                            ft.IconButton(ft.Icons.DELETE_SWEEP, icon_color=COLOR_ERROR, icon_size=22, tooltip="Clear All", on_click=clear_text),
                        ], spacing=0)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                text_input,
                ft.Row([char_count_text], alignment=ft.MainAxisAlignment.END),
            ],
            spacing=15,
        )
    )

    voice_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(key=v, text=k) for k, v in VOICE_PROFILES.items()],
        value="my-MM-NilarNeural",
        bgcolor="#1A1D24",
        fill_color=GLASS_INPUT_BG,
        border_color=GLASS_BORDER,
        color=COLOR_TEXT,
        text_size=14,
        border_radius=12,
        content_padding=15,
    )

    rate_slider = ft.Slider(
        min=-50, max=50, divisions=100, value=0, label="{value}%",
        active_color=COLOR_GOLD, inactive_color="#44FFFFFF",
    )
    
    pitch_slider = ft.Slider(
        min=-30, max=30, divisions=60, value=0, label="{value}Hz",
        active_color=COLOR_GOLD, inactive_color="#44FFFFFF",
    )

    # WebView ကို သိမ်းထားမယ့် Variable
    audio_webview = ft.WebView(expand=True)
    player_visible = False

    def play_audio_html(b64_str):
        # HTML5 Audio Player ကို တည်ဆောက်မယ်
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ background-color: #1A1D24; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                audio {{ width: 90%; }}
            </style>
        </head>
        <body>
            <audio controls autoplay>
                <source src="data:audio/mp3;base64,{b64_str}" type="audio/mp3">
                သင့်ဖုန်းက အသံကို မဖွင့်နိုင်ပါဘူး။
            </audio>
        </body>
        </html>
        """
        audio_webview.html = html_content
        audio_webview.update()

    def preview_voice(e):
        nonlocal is_previewing
        if is_previewing: return
        is_previewing = True
        status_text.value = "အသံစမ်းသပ်နေသည်..."
        page.update()

        selected_voice = voice_dropdown.value
        rate_str = f"{int(rate_slider.value):+d}%"
        pitch_str = f"{int(pitch_slider.value):+d}Hz"
        
        async def run_preview():
            try:
                cache_dir = os.path.join(os.getcwd(), "temp_tts")
                os.makedirs(cache_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime("%H%M%S")
                preview_path = os.path.join(cache_dir, f"preview_{timestamp}.mp3")
                
                preview_text = "မင်္ဂလာပါ၊ ကျွန်တော်တို့ Platinum Voice မှ ကြိုဆိုပါတယ်။ ဒါက အသံစမ်းသပ်နေတာ ဖြစ်ပါတယ်။"
                
                communicate = edge_tts.Communicate(preview_text, selected_voice, rate=rate_str, pitch=pitch_str)
                await communicate.save(preview_path)
                
                # Base64 ပြောင်းပြီး HTML Player ဆီ ပို့မယ်
                with open(preview_path, "rb") as f:
                    b64_str = base64.b64encode(f.read()).decode('utf-8')
                
                play_audio_html(b64_str)
                status_text.value = "အသံဖွင့်နေသည်..."
            except Exception as ex:
                status_text.value = f"Error: {str(ex)}"
            finally:
                is_previewing = False
                page.update()
                
        page.run_task(run_preview)

    preview_btn = ft.Button(
        content=ft.Text("Preview"),
        icon=ft.Icons.VOLUME_UP,
        bgcolor="transparent",
        color=COLOR_GOLD,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            side=ft.BorderSide(1, COLOR_GOLD),
        ),
        on_click=preview_voice,
        expand=True,
    )

    pronun_btn = ft.Button(
        content=ft.Text("အသံထွက် ပြင်ရန်"),
        icon=ft.Icons.RECORD_VOICE_OVER,
        bgcolor="transparent",
        color=COLOR_GOLD,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            side=ft.BorderSide(1, COLOR_GOLD),
        ),
        on_click=show_pronun_dialog,
        expand=True,
    )

    preset_name_input = ft.TextField(
        hint_text="သတ်မှတ်ချက် အမည်ပေးပါ (ဥပမာ - ရွှေစင်)",
        bgcolor=GLASS_INPUT_BG,
        border_color="transparent",
        color=COLOR_TEXT,
        text_size=14,
        content_padding=15,
        border_radius=10,
    )

    presets_list_container = ft.Column(spacing=10)

    def update_presets_ui():
        presets_list_container.controls.clear()
        if not presets_data:
            presets_list_container.controls.append(
                ft.Text("သိမ်းထားသော သတ်မှတ်ချက် မရှိပါ။", size=12, color=COLOR_TEXT_MUTED, italic=True)
            )
        else:
            for p_name, p_data in presets_data.items():
                def make_apply(p_name=p_name, p_data=p_data):
                    return lambda e: apply_preset(p_name, p_data)
                
                def make_delete(p_name=p_name):
                    return lambda e: delete_preset(p_name)

                row = ft.Row(
                    [
                        ft.Text(p_name, color=COLOR_GOLD, weight=ft.FontWeight.BOLD, expand=True),
                        ft.IconButton(ft.Icons.PLAY_ARROW, icon_color=COLOR_TEXT, icon_size=20, tooltip="သုံးမည်", on_click=make_apply()),
                        ft.IconButton(ft.Icons.DELETE, icon_color=COLOR_ERROR, icon_size=20, tooltip="ဖျက်မည်", on_click=make_delete()),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                presets_list_container.controls.append(row)
        page.update()

    def save_preset(e):
        name = preset_name_input.value.strip()
        if not name:
            status_text.value = "ကျေးဇူးပြု၍ သတ်မှတ်ချက် အမည်ပေးပါ။"
            page.update()
            return
        
        presets_data[name] = {
            "voice": voice_dropdown.value,
            "rate": rate_slider.value,
            "pitch": pitch_slider.value
        }
        save_presets_to_storage(presets_data)
        preset_name_input.value = ""
        status_text.value = f"'{name}' ကို သိမ်းဆည်းပြီးပါပြီ။"
        update_presets_ui()

    def apply_preset(name, data):
        voice_dropdown.value = data["voice"]
        rate_slider.value = data["rate"]
        pitch_slider.value = data["pitch"]
        status_text.value = f"'{name}' သတ်မှတ်ချက်ကို အသုံးပြုနေသည်။"
        page.update()

    def delete_preset(name):
        if name in presets_data:
            del presets_data[name]
            save_presets_to_storage(presets_data)
            status_text.value = f"'{name}' ကို ဖျက်လိုက်ပါပြီ။"
            update_presets_ui()

    save_preset_btn = ft.Button(
        content=ft.Text("Save Preset"),
        icon=ft.Icons.SAVE,
        bgcolor=COLOR_GOLD,
        color="#000000",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        on_click=save_preset,
    )

    settings_card = glass_card(
        ft.Column(
            [
                ft.Row([ft.Icon(ft.Icons.TUNE, color=COLOR_GOLD, size=22), ft.Text("VOICE SETTINGS", size=14, weight=ft.FontWeight.BOLD, color=COLOR_TEXT)]),
                ft.Text("ဘာသာစကား ရွေးချယ်ပါ", size=12, color=COLOR_TEXT_MUTED),
                voice_dropdown,
                
                ft.Text("Speed (အမြန်နှုန်း)", size=12, color=COLOR_TEXT_MUTED),
                rate_slider,
                
                ft.Text("Pitch (အသံအနိမ့်အမြင့်)", size=12, color=COLOR_TEXT_MUTED),
                pitch_slider,

                ft.Row(
                    [preview_btn, pronun_btn], 
                    alignment=ft.MainAxisAlignment.CENTER, 
                    spacing=10
                ),

                ft.Divider(color=GLASS_BORDER),
                ft.Text("သတ်မှတ်ချက် သိမ်းဆည်းရန်", size=12, color=COLOR_TEXT_MUTED),
                
                ft.Column(
                    [
                        preset_name_input,
                        ft.Row([save_preset_btn], alignment=ft.MainAxisAlignment.END)
                    ],
                    spacing=10
                ),
                
                ft.Divider(color=GLASS_BORDER),
                ft.Text("သိမ်းထားသော သတ်မှတ်ချက်များ", size=12, weight=ft.FontWeight.BOLD, color=COLOR_GOLD),
                presets_list_container,
            ],
            spacing=15,
        )
    )

    status_text = ft.Text("", size=14, color=COLOR_GOLD, text_align=ft.TextAlign.CENTER)
    progress_bar = ft.ProgressBar(width=350, color=COLOR_GOLD, bgcolor=GLASS_INPUT_BG, visible=False, border_radius=10)
    
    # Player Container (WebView ပါဝင်မယ်)
    player_container = ft.Column(visible=False, spacing=10)
    
    generate_btn = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.PLAY_CIRCLE_FILL, color="#000000"),
                ft.Text("GENERATE VOICE", size=16, weight=ft.FontWeight.BOLD, color="#000000"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=COLOR_GOLD,
        padding=ft.Padding.symmetric(vertical=18, horizontal=30),
        border_radius=16,
        shadow=ft.BoxShadow(blur_radius=20, color="#80FFD700", offset=ft.Offset(0, 5)),
        on_click=lambda e: page.run_task(generate_tts_process, e),
    )

    async def generate_tts_process(e):
        nonlocal is_generating
        if is_generating: return
        
        user_text = text_input.value
        if not user_text or not user_text.strip():
            status_text.value = "ကျေးဇူးပြု၍ စာသားထည့်ပါ။"
            page.update()
            return

        processed_text = user_text
        for word, replacement in pronunciations_data.items():
            processed_text = processed_text.replace(word, replacement)

        is_generating = True
        generate_btn.opacity = 0.5 
        generate_btn.disabled = True
        progress_bar.visible = True
        player_container.visible = False
        status_text.value = "စာသားများကို ခွဲထုတ်နေသည်..."
        page.update()

        try:
            chunks = split_unlimited_text(processed_text, max_chunk_size=2000)
            total_chunks = len(chunks)
            if total_chunks == 0: raise ValueError("စာသားမရှိပါ။")

            cache_dir = os.path.join(os.getcwd(), "temp_tts")
            os.makedirs(cache_dir, exist_ok=True)
            
            selected_voice = voice_dropdown.value
            rate_str = f"{int(rate_slider.value):+d}%"
            pitch_str = f"{int(pitch_slider.value):+d}Hz"
            
            chunk_files = []
            for i, chunk in enumerate(chunks):
                status_text.value = f"အပိုင်း {i+1}/{total_chunks} ကို ထုတ်လုပ်နေသည်... ({int((i/total_chunks)*100)}%)"
                page.update()
                
                chunk_file = os.path.join(cache_dir, f"chunk_{i}.mp3")
                communicate = edge_tts.Communicate(
                    chunk, 
                    selected_voice, 
                    rate=rate_str, 
                    pitch=pitch_str
                )
                await communicate.save(chunk_file)
                chunk_files.append(chunk_file)
                
                progress_bar.value = (i + 1) / total_chunks
                page.update()

            status_text.value = "အသံဖိုင်များကို ပေါင်းစပ်နေသည်..."
            page.update()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_filename = f"Platinum_TTS_{timestamp}.mp3"
            final_path = os.path.join(cache_dir, final_filename)
            
            if merge_audio_files(chunk_files, final_path):
                status_text.value = "အသံထုတ်လုပ်မှု ပြီးစီးပါပြီ!"
                setup_player_ui(final_path, final_filename)
            else:
                raise Exception("ဖိုင်များ ပေါင်းစပ်ရာတွင် အမှားအယွင်းရှိပါသည်။")

        except Exception as ex:
            status_text.value = f"အမှားအယွင်း: {str(ex)}"
        finally:
            is_generating = False
            generate_btn.opacity = 1.0
            generate_btn.disabled = False
            progress_bar.visible = False
            page.update()

    def setup_player_ui(file_path, filename):
        default_name = filename.replace(".mp3", "")
        file_name_input = ft.TextField(
            value=default_name,
            hint_text="ဖိုင်နာမည် ရိုက်ထည့်ပါ",
            bgcolor=GLASS_INPUT_BG,
            border_color=GLASS_BORDER,
            color=COLOR_TEXT,
            text_size=14,
            content_padding=10,
            border_radius=10,
        )

        def play_audio(e):
            try:
                with open(file_path, "rb") as f:
                    b64_str = base64.b64encode(f.read()).decode('utf-8')
                
                play_audio_html(b64_str)
                status_text.value = "အသံဖွင့်နေသည်..."
                page.update()
            except Exception as ex:
                status_text.value = f"ဖွင့်မရပါ: {str(ex)}"
                page.update()

        def save_to_download(e):
            try:
                custom_name = file_name_input.value.strip()
                custom_name = re.sub(r'[\\/*?:"<>|]', "", custom_name)
                
                if custom_name:
                    safe_filename = f"{custom_name}.mp3"
                else:
                    safe_filename = filename

                download_dir = "/storage/emulated/0/Download"
                if not os.path.exists(download_dir):
                    download_dir = os.path.expanduser("~/Downloads")
                    if not os.path.exists(download_dir):
                        os.makedirs(download_dir, exist_ok=True)

                dest_path = os.path.join(download_dir, safe_filename)
                shutil.copy2(file_path, dest_path)
                status_text.value = f"သိမ်းဆည်းပြီးပါပြီ: Download/{safe_filename}"
                page.update()
            except Exception as ex:
                status_text.value = f"သိမ်းဆည်းမှု အမှားအယွင်း: {str(ex)}"
                page.update()

        play_btn = ft.Button(
            content=ft.Text("Play Audio"),
            icon=ft.Icons.PLAY_ARROW,
            bgcolor=COLOR_GOLD,
            color="#000000",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            on_click=play_audio,
        )

        save_btn = ft.Button(
            content=ft.Text("Save to Download"),
            icon=ft.Icons.DOWNLOAD, 
            bgcolor="transparent",
            color=COLOR_TEXT,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                side=ft.BorderSide(1, COLOR_GOLD),
            ),
            on_click=save_to_download,
        )

        player_container.controls = [
            glass_card(
                ft.Column(
                    [
                        ft.Text("GENERATED AUDIO", size=12, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MUTED),
                        
                        ft.Text("ဖိုင်နာမည် ပြင်ဆင်ရန်", size=12, color=COLOR_TEXT_MUTED),
                        file_name_input,
                        
                        ft.Row([play_btn, save_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                )
            ),
            # WebView Player ကို ဒီနေရာမှာ ထည့်ထားပါတယ်
            ft.Container(
                content=audio_webview,
                height=80, # Player အမြင့်
                border_radius=10,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            )
        ]
        player_container.visible = True
        page.update()

    donate_btn = ft.TextButton(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.LOCAL_CAFE, color=COLOR_GOLD, size=18),
                ft.Text("Buy me a coffee", color=COLOR_GOLD, size=14),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        on_click=show_qr,
    )

    page.add(
        ft.Container(height=20),
        header,
        ft.Container(height=30),
        editor_card,
        ft.Container(height=20),
        settings_card,
        ft.Container(height=30),
        generate_btn,
        ft.Container(height=15),
        ft.Row([progress_bar], alignment=ft.MainAxisAlignment.CENTER),
        status_text,
        player_container,
        ft.Container(height=20),
        ft.Row([donate_btn], alignment=ft.MainAxisAlignment.CENTER),
        ft.Container(height=20),
        ft.Text("Developed By Dexter Syntax", size=12, color=COLOR_TEXT_MUTED, italic=True, text_align=ft.TextAlign.CENTER),
        ft.Container(height=20),
    )

    load_data()

if __name__ == "__main__":
    ft.run(main)
