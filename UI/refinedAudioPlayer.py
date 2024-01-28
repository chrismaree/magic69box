import vlc
import PySimpleGUI as sg
from sys import platform as PLATFORM
from os import listdir

PATH = './Assets/'
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
                 self.button('PLAY', BUTTON_DICT['PLAY_OFF']),
                 self.button('STOP', BUTTON_DICT['STOP']),
                 self.button('SOUND', BUTTON_DICT['SOUND_ON']),
                 self.button('PLUS', BUTTON_DICT['PLUS'])]]

        # Main GUI layout
        main_layout = [
            # Element for tracking elapsed time
            [sg.Text('00:00', key='TIME_ELAPSED'),
             sg.Slider(range=(0, 1), enable_events=True, resolution=0.0001, disable_number_display=True,
                       background_color='#83D8F5', orientation='h', key='TIME'),
             sg.Text('00:00', key='TIME_TOTAL')],

            # Button layout (created above)
            [sg.Column(col1)]]

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

        media = self.instance.media_new(track)
        media.set_meta(0, track.replace('\\', '/').split('/').pop())  # filename
        media.set_meta(1, 'Local Media')  # Default author value for local media
        self.media_list.add_media(media)
        self.track_cnt = self.media_list.count()

    def get_meta(self, meta_type):
        """ Retrieve saved meta data from tracks in media list """
        media = self.player.get_media()
        return media.get_meta(meta_type)

    def get_track_info(self):
        """ Show title and elapsed time if audio is loaded and playing """
        time_elapsed = "{:02d}:{:02d}".format(*divmod(self.player.get_time() // 1000, 60))
        time_total = "{:02d}:{:02d}".format(*divmod(self.player.get_length() // 1000, 60))
        if self.player.is_playing():
            message = "{}".format(self.get_meta(0))
            self.window['TIME_ELAPSED'].update(time_elapsed)
            self.window['TIME'].update(self.player.get_position())
            self.window['TIME_TOTAL'].update(time_total)

    def play(self):
        """ Called when the play button is pressed """
        if self.track_cnt > 0:  # Only play if there is a track loaded
            self.list_player.play()
            self.window['PLAY'].update(image_filename=BUTTON_DICT['PLAY_ON'])
            self.window['PAUSE'].update(image_filename=BUTTON_DICT['PAUSE_OFF'])

    def stop(self):
        """ Called when the stop button is pressed """
        self.player.stop()
        self.window['PLAY'].update(image_filename=BUTTON_DICT['PLAY_OFF'])
        self.window['PAUSE'].update(image_filename=BUTTON_DICT['PAUSE_OFF'])
        self.window['TIME'].update(value=0)
        self.window['TIME_ELAPSED'].update('00:00')

    def pause(self):
        """ Called when the pause button is pressed """
        self.window['PAUSE'].update(
            image_filename=BUTTON_DICT['PAUSE_ON'] if self.player.is_playing() else BUTTON_DICT['PAUSE_OFF'])
        self.window['PLAY'].update(
            image_filename=BUTTON_DICT['PLAY_OFF'] if self.player.is_playing() else BUTTON_DICT['PLAY_ON'])
        self.player.pause()

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

def main():
    """ The main program function """

    # Create the media player
    mp = MediaPlayer(size=(1920, 1080), scale=0.5)

    # Main event loop
    while True:
        event, values = mp.window.read(timeout=1000)
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


if __name__ == '__main__':
    main()
