import PySimpleGUI as sg
import pygame
import threading
import time

# Function to control audio playback
def play_audio(file, play_event, pause_event, progress_callback, done_callback):
    pygame.mixer.init()
    pygame.mixer.music.load(file)
    total_length = pygame.mixer.Sound(file).get_length()
    pygame.mixer.music.play()  # Start playing the music

    while pygame.mixer.music.get_busy():
        if pause_event.is_set():
            pygame.mixer.music.pause()
            pause_event.clear()  # Clear the pause event after pausing
            play_event.wait()  # Wait for the play event to continue
            pygame.mixer.music.unpause()
        current_pos = pygame.mixer.music.get_pos() / 1000
        progress_callback(current_pos, total_length)
        time.sleep(0.1)
    
    done_callback()

# Initialize Pygame mixer
pygame.mixer.init()

# Define GUI layout
layout = [
    [sg.Text("Magix69 Encoder")],
    [sg.Input(key="-FILE-", disabled=True), sg.FileBrowse(file_types=(("MP3 Files", "*.mp3"),))],
    [sg.Button("Play", key="-PLAY-PAUSE-")],
    [sg.ProgressBar(max_value=100, orientation='h', size=(100, 20), key='-PROGRESS-', expand_x=True)],
    [sg.Text('0:00', key='-CURRENT_TIME-', size=(8, 1)), sg.Text('', key='-MIDDLE_TIME-', size=(8, 1), justification='center', pad=((0,0),(0,0))), sg.Text('', key='-TOTAL_TIME-', size=(8, 1), justification='right', pad=((0,0),(0,0)))]
]

# Create window
window = sg.Window("Magix69 Encoder!!", layout, size=(500, 500))

# Event handling
play_event = threading.Event()
pause_event = threading.Event()
audio_thread = None

def reset_progress_bar():
    window['-PROGRESS-'].update_bar(0, max=100)
    window['-CURRENT_TIME-'].update('0:00')
    window['-MIDDLE_TIME-'].update('')
    window['-TOTAL_TIME-'].update('')
    global audio_thread
    audio_thread = None

def update_progress_bar(current_pos, total_length):
    progress = (current_pos / total_length) * 100
    window['-PROGRESS-'].update_bar(progress, max=100)
    window['-MIDDLE_TIME-'].update(format_time(current_pos))
    window['-TOTAL_TIME-'].update(format_time(total_length))

def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f'{minutes}:{seconds:02}'

while True:
    event, values = window.read(timeout=100)

    if event == sg.WIN_CLOSED:
        break
    elif event == "-PLAY-PAUSE-":
        if audio_thread is None:
            # Start playing
            play_event.set()
            window['-PLAY-PAUSE-'].update('Pause')
            audio_thread = threading.Thread(target=play_audio, args=(
                values["-FILE-"], play_event, pause_event,
                update_progress_bar,
                reset_progress_bar), daemon=True)
            audio_thread.start()
        else:
            # Toggle play/pause
            if not pause_event.is_set():
                pause_event.set()
                pygame.mixer.music.pause()  # Pause the music
                window['-PLAY-PAUSE-'].update('Play')
            else:
                play_event.set()
                pygame.mixer.music.unpause()  # Unpause the music
                window['-PLAY-PAUSE-'].update('Pause')

    elif event == "-FILE-":
        # Update labels based on the size of the imported audio file
        total_length = pygame.mixer.Sound(values["-FILE-"]).get_length()
        window['-TOTAL_TIME-'].update(format_time(total_length))

window.close()
