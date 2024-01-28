import vlc
import PySimpleGUI as sg
from sys import platform as PLATFORM
from os import listdir
import json
import os
import sys

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS.
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

PATH = os.path.join(base_path, "./Assets/")

# PATH = './Assets/'
BUTTON_DICT = {img[:-4].upper(): PATH + img for img in listdir(PATH)}
ICON = PATH + 'player.ico'


class MediaPlayer:

    def __init__(self, size, scale=1.0, theme='LightGreen'):
        """ Media player constructor """

        # Setup media player
        self.instance = vlc.Instance()
        self.list_player = self.instance.media_list_player_new()
        self.media_list = self.instance.media_list_new([])
        self.list_player.set_media_list(self.media_list)
        self.player = self.list_player.get_media_player()

        self.track_cnt = 0  # Count of tracks loaded into `media_list`
        self.track_num = 0  # Index of the track currently playing

        # Setup GUI window for output of media
        self.theme = theme
        self.default_bg_color = sg.LOOK_AND_FEEL_TABLE[self.theme]['BACKGROUND']
        self.hover_color = '#6B8E23'  # Slightly darker shade of LightGreen
        self.window_size = size
        self.player_size = [x*scale for x in size]
        self.window = self.create_window()
        self.check_platform()

        # Unmute the volume if muted
        if self.player.audio_get_mute():
            self.toggle_mute()

    def button(self, key, image, **kwargs):
        """ Create media player button """
        return sg.Button(image_filename=image, border_width=0, pad=(0, 0), key=key,
                         button_color=(self.hover_color, self.default_bg_color))  # Swapped colors for hover effect

    def create_window(self):
        """ Create GUI instance """
        sg.change_look_and_feel(self.theme)

        # Column layout for media player button controls
        col1 = [[self.button('SKIP PREVIOUS', BUTTON_DICT['START']),
                 self.button('PAUSE', BUTTON_DICT['PAUSE_OFF']),
                 self.button('PLAY', BUTTON_DICT['PLAY_OFF'], button_color=('white', 'green'), bind_return_key=True),
                 self.button('STOP', BUTTON_DICT['STOP']),
                 self.button('SOUND', BUTTON_DICT['SOUND_ON']),
                 self.button('PLUS', BUTTON_DICT['PLUS'])]]

        # Column layout for effects
        col2 = [[sg.Button('Add effect', key='ADD_EFFECT', visible=True),
                 sg.Button('Remove effect', key='REMOVE_EFFECT', visible=True),
                 sg.Button('Export', key='EXPORT', visible=True),
                 sg.Combo(['Affect1', 'Affect2', 'Affect3'], key='EFFECTS', default_value='Affect1', visible=True)],
                [sg.Table(values=[], headings=['Timestamp', 'Effect'], display_row_numbers=True, 
                          key='EFFECTS_TABLE', visible=True, size=(self.window_size[0], 10), enable_events=True)]]

        # Main GUI layout
        main_layout = [
            # Element for tracking elapsed time
            [sg.Text('00:00:00', key='TIME_ELAPSED'),
             sg.Slider(range=(0, 1), enable_events=True, resolution=0.0001, disable_number_display=True,
                       background_color='#83D8F5', orientation='h', key='TIME'),
             sg.Text('00:00:00', key='TIME_TOTAL', visible=True)],

            # Button layout (created above)
            [sg.Column(col1, size=(self.window_size[0]*0.5, 60), pad=(0,0))],
            [sg.HorizontalSeparator()],
            [sg.Column(col2, visible=True, pad=(0,0))],
            [sg.Text('', key='ENCODING_STATUS', text_color='green', visible=False)]]

        # Create a PySimpleGUI window from the specified parameters
        window = sg.Window('69 Box Encoder', main_layout, element_justification='center', icon=ICON, finalize=True)

        # Expand the time element so that the row elements are positioned correctly
        window['TIME'].expand(expand_x=True)
        return window

    def check_platform(self):
        """ Platform specific adjustments for window handler """
        if PLATFORM.startswith('linux'):
            self.player.set_xwindow(self.window.TKroot.winfo_id())
        else:
            self.player.set_hwnd(self.window.TKroot.winfo_id())

    def add_media(self, track=None):
        """ Add new track to list player """
        if track is None:
            return  # User did not provide any information

        # Stop the current track before adding a new one
        self.player.stop()
        self.window['PLAY'].update(image_filename=BUTTON_DICT['PLAY_OFF'])
        self.window['PAUSE'].update(image_filename=BUTTON_DICT['PAUSE_OFF'])
        self.window['TIME'].update(value=0)
        self.window['TIME_ELAPSED'].update('00:00:00')

        # Clear the media list before adding a new track
        self.media_list = self.instance.media_list_new([])
        self.list_player.set_media_list(self.media_list)

        media = self.instance.media_new(track)
        media.set_meta(0, track.replace('\\', '/').split('/').pop())  # filename
        media.set_meta(1, 'Local Media')  # Default author value for local media
        self.media_list.add_media(media)
        self.track_cnt = self.media_list.count()
        self.track_num = self.track_cnt - 1  # Update the track number to the newly added track

        # Check if the track is already in the Encodings.json file
        try:
            with open('Encodings.json', 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = []

        existing_entry = next((item for item in data if item["filename"] == media.get_meta(0)), None)
        if existing_entry:
            # Update the status text and make it visible
            self.window['ENCODING_STATUS'].update('Editing an existing encoding: {}'.format(media.get_meta(0)))
            self.window['ENCODING_STATUS'].update(visible=True, text_color='red')
            # Pre-populate the table with the existing effects
            self.window['EFFECTS_TABLE'].update(values=existing_entry["effects"])
        else:
            # Update the status text and make it visible
            self.window['ENCODING_STATUS'].update('Creating a new encoding: {}'.format(media.get_meta(0)))
            self.window['ENCODING_STATUS'].update(visible=True, text_color='green')
            # Empty the table
            self.window['EFFECTS_TABLE'].update(values=[])

        # Auto play the added track
        self.list_player.play_item_at_index(self.track_num)
        self.window['TIME'].update(value=0)
        self.window['TIME_ELAPSED'].update('00:00:00')

    def get_meta(self, meta_type):
        """ Retrieve saved meta data from tracks in media list """
        media = self.player.get_media()
        return media.get_meta(meta_type)

    def get_track_info(self):
        """ Show title and elapsed time if audio is loaded and playing """
        time_elapsed = "{:02d}:{:02d}:{:03d}".format(*divmod(self.player.get_time() // 1000, 60), self.player.get_time() % 1000)
        time_total = "{:02d}:{:02d}:{:03d}".format(*divmod(self.player.get_length() // 1000, 60), self.player.get_length() % 1000)
        if self.player.is_playing():
            message = "{}".format(self.get_meta(0))
            self.window['TIME_ELAPSED'].update(time_elapsed)
            self.window['TIME_TOTAL'].update(time_total)

    def play(self):
        """ Called when the play button is pressed """
        if self.track_cnt > 0:  # Only play if there is a track loaded
            if self.player.is_playing():
                self.player.pause()
                self.window['PLAY'].update(image_filename=BUTTON_DICT['PLAY_OFF'])
                self.window['PAUSE'].update(image_filename=BUTTON_DICT['PAUSE_ON'])
            else:
                self.player.play()
                self.window['PLAY'].update(image_filename=BUTTON_DICT['PLAY_ON'])
                self.window['PAUSE'].update(image_filename=BUTTON_DICT['PAUSE_OFF'])

    def pause(self):
        """ Called when the pause button is pressed """
        if self.player.is_playing():
            self.player.pause()
            self.window['PAUSE'].update(image_filename=BUTTON_DICT['PAUSE_ON'])
            self.window['PLAY'].update(image_filename=BUTTON_DICT['PLAY_OFF'])
        else:
            self.player.play()
            self.window['PAUSE'].update(image_filename=BUTTON_DICT['PAUSE_OFF'])
            self.window['PLAY'].update(image_filename=BUTTON_DICT['PLAY_ON'])

    def stop(self):
        """ Called when the stop button is pressed """
        self.player.stop()
        self.window['PLAY'].update(image_filename=BUTTON_DICT['PLAY_OFF'])
        self.window['PAUSE'].update(image_filename=BUTTON_DICT['PAUSE_OFF'])
        self.window['TIME'].update(value=0)
        self.window['TIME_ELAPSED'].update('00:00:00')

    def skip_previous(self):
        """ Called when the skip previous button is pressed """
        self.list_player.previous()
        self.reset_pause_play()
        if not self.track_num == 1:
            self.track_num -= 1

    def reset_pause_play(self):
        """ Reset pause play buttons after skipping tracks """
        self.window['PAUSE'].update(image_filename=BUTTON_DICT['PAUSE_OFF'])
        self.window['PLAY'].update(image_filename=BUTTON_DICT['PLAY_ON'])

    def toggle_mute(self):
        """ Called when the sound button is pressed """
        self.window['SOUND'].update(
            image_filename=BUTTON_DICT['SOUND_ON'] if self.player.audio_get_mute() else BUTTON_DICT['SOUND_OFF'])
        self.player.audio_set_mute(not self.player.audio_get_mute())

    def load_single_track(self):
        """ Open a file browser directly to select a single track """
        track = sg.popup_get_file('Browse for local media:', no_window=True, file_types=(("Audio Files", "*.mp3;*.wav;*.ogg;*.flac"),))
        if track:
            self.add_media(track)

    def add_effect(self):
        """ Add an effect to the effects table """
        effect = self.window['EFFECTS'].get()
        timestamp = "{:02d}:{:02d}:{:03d}".format(*divmod(self.player.get_time() // 1000, 60), self.player.get_time() % 1000)
        self.window['EFFECTS_TABLE'].update(values=self.window['EFFECTS_TABLE'].get() + [[timestamp, effect]])

    def remove_effect(self):
        """ Remove an effect from the effects table """
        selected_rows = self.window['EFFECTS_TABLE'].SelectedRows
        if selected_rows:
            table_data = self.window['EFFECTS_TABLE'].get()
            for row in sorted(selected_rows, reverse=True):
                del table_data[row]
            self.window['EFFECTS_TABLE'].update(values=table_data)

    def move_to_timestamp(self, timestamp):
        """ Move the audio to the selected timestamp """
        minutes, seconds, milliseconds = map(int, timestamp.split(':'))
        time_in_milliseconds = (minutes * 60 + seconds) * 1000 + milliseconds
        self.player.set_time(time_in_milliseconds)
        self.window['TIME'].update(value=self.player.get_position())  # Update the dragger/progress bar
        self.get_track_info()  # Update the UI timer immediately after moving the audio

    def export_effects(self):
        """ Export the effects to a JSON file """
        filename = self.get_meta(0)  # Get the filename of the current track
        effects = self.window['EFFECTS_TABLE'].get()  # Get the effects from the table
        encodings_file_path = os.path.join(self.get_application_path(), 'Encodings.json')

        # Load the existing data from the JSON file
        try:
            with open(encodings_file_path, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = []

        # Check if the filename already exists in the data
        existing_entry = next((item for item in data if item["filename"] == filename), None)
        if existing_entry:
            # Replace the existing entry with the new effects
            existing_entry["effects"] = effects
        else:
            # Append the new data
            data.append({
                'filename': filename,
                'effects': effects
            })

        # Write the data back to the JSON file
        with open(encodings_file_path, 'w') as file:
            json.dump(data, file, indent=4)

    def get_application_path(self):
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            return os.path.dirname(sys.executable)
        else:
            # Running in a normal Python environment
            return os.path.dirname(os.path.abspath(__file__))


def main():
    """ The main program function """

    # Create the media player
    mp = MediaPlayer(size=(720, 100), scale=1)

    # Main event loop
    while True:
        event, values = mp.window.read(timeout=1)  # Reduced timeout for more frequent updates
        mp.get_track_info()
        if event in (None, 'Exit'):
            break
        if event == 'PLAY':
            mp.play()
        if event == 'PAUSE':
            mp.pause()
        if event == 'SKIP PREVIOUS':
            mp.skip_previous()
        if event == 'STOP':
            mp.stop()
        if event == 'SOUND':
            mp.toggle_mute()
        if event == 'TIME':
            # Check if the player is playing before setting the position
            if mp.player.is_playing():
                mp.player.set_position(values['TIME'])
        if event == 'PLUS':
            mp.load_single_track()
        if event == 'ADD_EFFECT':
            mp.add_effect()
        if event == 'REMOVE_EFFECT':
            mp.remove_effect()
        if event == 'EFFECTS_TABLE':
            # Check if the table has at least one row selected
            if values['EFFECTS_TABLE']:
                # Get the first selected row index
                selected_row_index = values['EFFECTS_TABLE'][0]
                # Retrieve the timestamp from the selected row
                timestamp = mp.window['EFFECTS_TABLE'].get()[selected_row_index][0]
                mp.move_to_timestamp(timestamp)
        if event == 'EXPORT':
            mp.export_effects()


if __name__ == '__main__':
    main()




