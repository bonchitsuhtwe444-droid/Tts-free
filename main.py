import flet as ft
import flet_audio as fta
import edge_tts
import asyncio
import re
import os
import shutil
from datetime import datetime

# ==========================================
# PLATINUM VOICE - PRODUCTION READY TTS APP
# ==========================================

COLOR_BG = "#0D0E12"
COLOR_CARD = "#1A1D24"
COLOR_GOLD = "#FFD700"
COLOR_PLATINUM = "#E5E4E2"
COLOR_TEXT_MUTED = "#8B8E96"
COLOR_ERROR = "#FF4D4D"

VOICES = {
    "မိန်းကလေးအသံ (နီလာ)": "my-MM-NilarNeural",
    "ယောက်ျားလေးအသံ (သီဟ)": "my-MM-ThihaNeural"
}

def split_unlimited_text(text: str, max_chunk_size: int = 2000) -> list[str]:
    if not text or not text.strip():
        return []
    paragraphs = re.split(r'\n\s*\n', text.strip())
    chunks = []
    current_chunk = ""
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
    page.bgcolor = COLOR_BG
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO
    
    page.fonts = {
        "Padauk": "https://github.com/google/fonts/raw/main/ofl/padauk/Padauk-Regular.ttf"
    }
    page.theme = ft.Theme(font_family="Padauk")

    is_generating = False
    generated_audio_path = None
    audio_player = None

    # 1. Header
    header = ft.Container(
        content=ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("PLATINUM VOICE", size=24, weight=ft.FontWeight.BOLD, color=COLOR_GOLD),
                        ft.Text("Unlimited Burmese Text-to-Speech", size=12, color=COLOR_TEXT_MUTED),
                    ],
                    spacing=2,
                ),
                ft.Container(
                    content=ft.Text("PRO", size=10, weight=ft.FontWeight.BOLD, color="#000000"),
                    bgcolor=COLOR_GOLD,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    border_radius=4,
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding.only(bottom=20),
    )

    # 2. Script Editor Card
    text_input = ft.TextField(
        multiline=True,
        min_lines=8,
        max_lines=15,
        hint_text="သင့်စာသားကို ဒီနေရာမှာ ရိုက်ထည့်ပါ သို့မဟုတ် Paste လုပ်ပါ...",
        bgcolor=COLOR_CARD,
        border_color=COLOR_PLATINUM,
        border_width=1,
        color=COLOR_PLATINUM,
        cursor_color=COLOR_GOLD,
        text_size=14,
        content_padding=15,
        border_radius=12,
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

    editor_card = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Script Editor", size=16, weight=ft.FontWeight.W_600, color=COLOR_PLATINUM),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE, 
                            icon_color=COLOR_ERROR,
                            icon_size=20,
                            tooltip="Clear All",
                            on_click=clear_text,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                text_input,
                ft.Row([char_count_text], alignment=ft.MainAxisAlignment.END),
            ],
            spacing=10,
        ),
        bgcolor=COLOR_CARD,
        padding=15,
        border_radius=16,
        border=ft.Border.all(1, "#33E5E4E2"),
    )

    # 3. Voice & Settings Card
    voice_dropdown = ft.Dropdown(
        label="အသံရွေးချယ်ပါ",
        options=[ft.dropdown.Option(key=v, text=k) for k, v in VOICES.items()],
        value="my-MM-NilarNeural",
        bgcolor=COLOR_BG,
        border_color=COLOR_PLATINUM,
        color=COLOR_PLATINUM,
        label_style=ft.TextStyle(color=COLOR_GOLD),
        text_size=14,
        border_radius=10,
    )

    rate_slider = ft.Slider(
        min=-50, max=50, divisions=100, value=0, label="{value}%",
        active_color=COLOR_GOLD, inactive_color=COLOR_TEXT_MUTED,
    )
    pitch_slider = ft.Slider(
        min=-30, max=30, divisions=60, value=0, label="{value}Hz",
        active_color=COLOR_GOLD, inactive_color=COLOR_TEXT_MUTED,
    )

    settings_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("Voice Settings", size=16, weight=ft.FontWeight.W_600, color=COLOR_PLATINUM),
                voice_dropdown,
                ft.Text("Speed (အမြန်နှုန်း)", size=12, color=COLOR_TEXT_MUTED),
                rate_slider,
                ft.Text("Pitch (အသံအနိမ့်အမြင့်)", size=12, color=COLOR_TEXT_MUTED),
                pitch_slider,
            ],
            spacing=10,
        ),
        bgcolor=COLOR_CARD,
        padding=15,
        border_radius=16,
        border=ft.Border.all(1, "#33E5E4E2"),
    )

    status_text = ft.Text("", size=14, color=COLOR_GOLD, text_align=ft.TextAlign.CENTER)
    progress_bar = ft.ProgressBar(width=300, color=COLOR_GOLD, bgcolor=COLOR_CARD, visible=False)
    player_container = ft.Column(visible=False, spacing=10)
    
    generate_btn = ft.Button(
        content=ft.Text("Generate Voice (အသံထုတ်မည်)", size=16, weight=ft.FontWeight.BOLD),
        icon=ft.Icons.PLAY_CIRCLE_FILLED, 
        bgcolor=COLOR_GOLD,
        color="#000000",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.Padding.symmetric(vertical=18, horizontal=30),
        ),
        width=300,
    )

    # --- Logic ---
    async def generate_tts_process(e):
        nonlocal is_generating, generated_audio_path, audio_player
        if is_generating: return
        
        user_text = text_input.value
        if not user_text or not user_text.strip():
            status_text.value = "ကျေးဇူးပြု၍ စာသားထည့်ပါ။"
            page.update()
            return

        is_generating = True
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
                generated_audio_path = final_path
                status_text.value = "အသံထုတ်လုပ်မှု ပြီးစီးပါပြီ!"
                setup_player(final_path, final_filename)
            else:
                raise Exception("ဖိုင်များ ပေါင်းစပ်ရာတွင် အမှားအယွင်းရှိပါသည်။")

        except Exception as ex:
            status_text.value = f"အမှားအယွင်း: {str(ex)}"
        finally:
            is_generating = False
            generate_btn.disabled = False
            progress_bar.visible = False
            page.update()

    def setup_player(file_path, filename):
        nonlocal audio_player
        
        # ရှိပြီးသား player ရှိရင် ဖျက်မယ်
        if audio_player:
            page.overlay.remove(audio_player)
        
        # Audio Player အသစ်ဆောက်မယ်
        audio_player = fta.Audio(src=file_path, autoplay=False, volume=1.0)
        page.overlay.append(audio_player)
        
        play_btn = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW, 
            icon_color=COLOR_GOLD,
            icon_size=40,
            on_click=lambda e: toggle_play(),
        )
        
        def toggle_play():
            if audio_player.is_playing():
                audio_player.pause()
                play_btn.icon = ft.Icons.PLAY_ARROW 
            else:
                audio_player.play()
                play_btn.icon = ft.Icons.PAUSE 
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

        save_btn = ft.Button(
            content=ft.Text("Save to Download"),
            icon=ft.Icons.DOWNLOAD, 
            bgcolor=COLOR_PLATINUM,
            color="#000000",
            on_click=save_to_download,
        )

        player_container.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Now Playing", size=14, color=COLOR_TEXT_MUTED),
                        ft.Text(filename, size=16, weight=ft.FontWeight.BOLD, color=COLOR_PLATINUM),
                        ft.Row([play_btn, save_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                bgcolor=COLOR_CARD,
                padding=20,
                border_radius=16,
                border=ft.Border.all(2, COLOR_GOLD), 
            )
        ]
        player_container.visible = True
        page.update()

    generate_btn.on_click = generate_tts_process

    page.add(
        header,
        editor_card,
        settings_card,
        ft.Container(height=10),
        ft.Row([generate_btn], alignment=ft.MainAxisAlignment.CENTER),
        ft.Container(height=10),
        ft.Row([progress_bar], alignment=ft.MainAxisAlignment.CENTER),
        status_text,
        player_container,
    )

if __name__ == "__main__":
    ft.run(main)
