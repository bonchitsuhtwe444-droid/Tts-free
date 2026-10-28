import flet as ft
import edge_tts
import asyncio
import re
import os
import shutil
from datetime import datetime

# ==========================================
# PLATINUM VOICE - GLASSMORPHISM UI (FINAL)
# ==========================================

GRADIENT_COLORS = ["#1A0B2E", "#2D1B4E", "#0F2027", "#203A43"] 
COLOR_GOLD = "#FFD700"
COLOR_TEXT = "#FFFFFF"
COLOR_TEXT_MUTED = "#B0BEC5"
COLOR_ERROR = "#FF5252"

GLASS_BG = "#22FFFFFF" 
GLASS_BORDER = "#44FFFFFF" 
GLASS_INPUT_BG = "#11000000" 

VOICES = {
    "မိန်းကလေးအသံ (နီလာ)": "my-MM-NilarNeural",
    "ယောက်ျားလေးအသံ (သီဟ)": "my-MM-ThihaNeural"
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
    page.scroll = ft.ScrollMode.AUTO
    
    page.fonts = {
        "Padauk": "https://github.com/google/fonts/raw/main/ofl/padauk/Padauk-Regular.ttf"
    }
    page.theme = ft.Theme(font_family="Padauk")

    page.bgcolor = ft.LinearGradient(
        begin=ft.Alignment.TOP_LEFT,
        end=ft.Alignment.BOTTOM_RIGHT,
        colors=GRADIENT_COLORS,
    )

    is_generating = False

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

    def show_qr(e):
        dlg = ft.AlertDialog(
            title=ft.Text("မုန့်ဖိုးပေးရန်", color=COLOR_GOLD, text_align=ft.TextAlign.CENTER),
            content=ft.Container(
                content=ft.Image(
                    src="kpay_qr.jpg", 
                    width=250, 
                    height=250, 
                    fit=ft.BoxFit.CONTAIN
                ),
                alignment=ft.Alignment.CENTER,
            ),
            actions=[ft.TextButton("ပိတ်မည်", on_click=lambda e: page.close(dlg))],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            bgcolor="#2D1B4E", 
            shape=ft.RoundedRectangleBorder(radius=20),
        )
        page.open(dlg)

    # 1. Header (letter_spacing ဖြုတ်ထားပါတယ်)
    header = ft.Row(
        [
            ft.Column(
                [
                    ft.Text("PLATINUM VOICE", size=26, weight=ft.FontWeight.W_900, color=COLOR_TEXT),
                    ft.Text("UNLIMITED TTS", size=12, weight=ft.FontWeight.BOLD, color=COLOR_GOLD),
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

    # 2. Script Editor
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

    editor_card = glass_card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.EDIT_NOTE, color=COLOR_GOLD, size=22),
                        ft.Text("SCRIPT EDITOR", size=14, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_SWEEP, 
                            icon_color=COLOR_ERROR,
                            icon_size=22,
                            tooltip="Clear All",
                            on_click=clear_text,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                text_input,
                ft.Row([char_count_text], alignment=ft.MainAxisAlignment.END),
            ],
            spacing=15,
        )
    )

    # 3. Voice Settings
    voice_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(key=v, text=k) for k, v in VOICES.items()],
        value="my-MM-NilarNeural",
        bgcolor=GLASS_INPUT_BG,
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

    settings_card = glass_card(
        ft.Column(
            [
                ft.Row([ft.Icon(ft.Icons.TUNE, color=COLOR_GOLD, size=22), ft.Text("VOICE SETTINGS", size=14, weight=ft.FontWeight.BOLD, color=COLOR_TEXT)]),
                ft.Text("အသံရွေးချယ်ပါ", size=12, color=COLOR_TEXT_MUTED),
                voice_dropdown,
                ft.Text("Speed (အမြန်နှုန်း)", size=12, color=COLOR_TEXT_MUTED),
                rate_slider,
                ft.Text("Pitch (အသံအနိမ့်အမြင့်)", size=12, color=COLOR_TEXT_MUTED),
                pitch_slider,
            ],
            spacing=10,
        )
    )

    status_text = ft.Text("", size=14, color=COLOR_GOLD, text_align=ft.TextAlign.CENTER)
    progress_bar = ft.ProgressBar(width=350, color=COLOR_GOLD, bgcolor=GLASS_INPUT_BG, visible=False, border_radius=10)
    player_container = ft.Column(visible=False, spacing=10)
    
    # Generate Button
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

    # --- Logic ---
    async def generate_tts_process(e):
        nonlocal is_generating
        if is_generating: return
        
        user_text = text_input.value
        if not user_text or not user_text.strip():
            status_text.value = "ကျေးဇူးပြု၍ စာသားထည့်ပါ။"
            page.update()
            return

        is_generating = True
        generate_btn.opacity = 0.5 
        generate_btn.disabled = True
        progress_bar.visible = True
        player_container.visible = False
        status_text.value = "စာသားများကို ခွဲထုတ်နေသည်..."
        page.update()

        try:
            chunks = split_unlimited_text(user_text, max_chunk_size=2000)
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
                communicate = edge_tts.Communicate(chunk, selected_voice, rate=rate_str, pitch=pitch_str)
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
        def play_audio(e):
            try:
                page.launch_url(f"file://{file_path}")
                status_text.value = "အသံဖွင့်နေသည်..."
                page.update()
            except Exception as ex:
                status_text.value = f"ဖွင့်မရပါ: {str(ex)}"
                page.update()

        def save_to_download(e):
            try:
                download_dir = "/storage/emulated/0/Download"
                if not os.path.exists(download_dir):
                    download_dir = os.path.expanduser("~/Downloads")
                    if not os.path.exists(download_dir):
                        os.makedirs(download_dir, exist_ok=True)

                dest_path = os.path.join(download_dir, filename)
                shutil.copy2(file_path, dest_path)
                status_text.value = f"သိမ်းဆည်းပြီးပါပြီ: Download/{filename}"
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
                        ft.Text(filename, size=14, weight=ft.FontWeight.BOLD, color=COLOR_GOLD),
                        ft.Row([play_btn, save_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                )
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
    )

if __name__ == "__main__":
    ft.run(main)
