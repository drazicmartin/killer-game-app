from kivy import Config
from kivy.app import App
from kivy.uix.button import Button
from kivy.core.window import Window
from functools import partial
from kivy.uix.screenmanager import ScreenManager, Screen
import pandas as pd
import numpy as np
from pdb import set_trace as bp

Window.fullscreen = True
Window.maximize()
Config.set('kivy', 'exit_on_escape', '0')

cycle = np.array([])

df = pd.read_csv("data.csv")
NB_PLAYER = len(df.index)


def string_chunks(string, x):
    new = ''
    cnt = 0
    for ch in string:
        if cnt%x==0 and cnt!=0: # checking if cnt is a multiple of x and not 0, we don't want to put star at index 0
            new += '\n'
        cnt += 1
        new += ch
    return new


# Declare both screens
class MainScreen(Screen):
    def on_leave(self, *args):
        self.ids.password.text = ""

    def on_pre_enter(self, *args):
        self.ids.playerGrid.clear_widgets()
        self.create_player_buttons()

    def create_player_buttons(self):
        for id, row in df.iterrows():
            txt = row["Prénom"] + " " + row["Nom de famille"]

            button = Button(text=txt, height=100, size_hint_y=None, on_press=partial(self.change_to_player_mission_screen, id))
            button.color = (1, 1, 1)
            button.font_size = 25
            if row['team'] == 'Bleu':
                button.background_color = (0, 0, 1, 1)
            elif row['team'] == 'Rouge':
                button.background_color = (1, 0, 0, 1)
            else:
                button.background_color = (1, 1, 1, 0.5)
            self.ids.playerGrid.add_widget(button)

    def change_to_player_mission_screen(self, player_id, m_button):
        player = df.iloc[player_id]
        if player['password'] == 'None' or player['password'] == '' or player['password'] is None:
            self.manager.transition.direction = 'left'
            self.manager.player_id = player_id
            self.manager.current = 'info'
        elif player['password'] == self.ids.password.text:
            self.manager.transition.direction = 'left'
            self.manager.player_id = player_id
            self.manager.current = 'mission'


class PlayerMissionScreen(Screen):
    def __init__(self, **kw):
        super(PlayerMissionScreen, self).__init__(**kw)
        self.player_id = None

    def on_pre_enter(self, *args):
        self.player_id = self.manager.player_id
        self.load_player_mission()

    def next_mission(self):
        df.loc[self.player_id, 'mission_completed'] += 1
        df.to_csv("data.csv", index=False)
        self.load_player_mission()

    def on_leave(self, *args):
        self.ids.label_name.text = ""

    def load_player_mission(self):
        player_info = df.iloc[self.player_id]
        self.ids.label_name.text = player_info['Prénom'] + " " + player_info['Nom de famille']
        target_info = df.iloc[int(df.loc[self.player_id, 'target_id'])]
        if player_info['lose'] == False:
            self.ids.label_current_target.text = "Votre cible est : " + target_info['Prénom'] + " " + target_info['Nom de famille']
            mission = string_chunks(player_info['mission'], 100)
            self.ids.label_mission.text = "Votre missions est de : {}".format(mission)
        else:
            self.ids.label_current_target.text = "Tu as perdu !"

    def _on_keyboard_down(self, instance, keyboard, keycode, text, modifiers):
        if modifiers[0] == 'escape':  # Escape
            self.manager.transition.direction = 'right'
            self.manager.player_id = None
            self.manager.current = 'main'


class PlayerInfoScreen(Screen):
    def __init__(self, **kw):
        super(PlayerInfoScreen, self).__init__(**kw)
        self.player_id = None
        self.selected_team = None

    def on_pre_enter(self, *args):
        self.player_id = self.manager.player_id
        player_info = df.iloc[self.player_id]
        self.ids.label_name.text = player_info['Prénom'] + " " + player_info['Nom de famille']

    def on_leave(self, *args):
        self.ids.label_team.text = 'Selectionne ton équipe : None'
        self.ids.set_password.text = ''
        self.selected_team = None

    def select_team(self, team):
        self.ids.label_team.text = "Selectionne ton équipe : {}".format(team)
        self.selected_team = team

    def validation(self):
        password = self.ids.set_password.text.strip()
        if password == '':
            return
        if self.selected_team is None:
            return
        df.loc[self.player_id, 'team'] = self.selected_team
        df.loc[self.player_id, 'password'] = self.ids.set_password.text.strip()
        df.to_csv("data.csv", index=False)
        self.manager.transition.direction = 'right'
        self.manager.player_id = None
        self.manager.current = 'main'


class MissionCompletedScreen(Screen):
    def __init__(self, **kw):
        super(MissionCompletedScreen, self).__init__(**kw)
        self.player_id = None

    def on_pre_enter(self, *args):
        self.player_id = self.manager.player_id

    def validation(self):
        player_info = df.iloc[self.player_id]

        if self.ids.target_password.text.strip() != df.loc[player_info['target_id'], 'password']:
            return

        df.loc[player_info['target_id'], 'lose'] = True
        df.loc[self.player_id, 'mission'] = df.loc[player_info['target_id'], 'mission']
        df.loc[self.player_id, 'target_id'] = df.loc[player_info['target_id'], 'target_id']
        df.to_csv('data.csv', index=False)

        self.manager.transition.direction = 'right'
        self.manager.current = 'mission'


class FreeGamesScreen(Screen):
    pass


class SGKApp(App):
    def build(self):
        # Create the screen manager
        self.sm = ScreenManager()

        self.my_keyboard = Window.request_keyboard(self.my_keyboard_down, self.root)
        self.my_keyboard.bind(on_key_down=self.my_keyboard_down)

        self.sm.add_widget(MainScreen(name='main'))
        self.sm.add_widget(PlayerMissionScreen(name='mission'))
        self.sm.add_widget(PlayerInfoScreen(name='info'))
        self.sm.add_widget(MissionCompletedScreen(name='mission_completed'))
        self.sm.add_widget(FreeGamesScreen(name='free_game'))

        return self.sm

    def my_keyboard_down(self, *args):
        if len(args) == 0:
            return
        else:
            keyboard = args[0]
            keycode = args[1]
            text = args[2]
            modifiers = args[3]
        if keycode[1] == 'escape':
            if self.sm.current == 'mission_completed':
                self.sm.transition.direction = "right"
                self.sm.current = "mission"
            elif self.sm.current == 'main':
                quit()
            else:
                self.sm.transition.direction = "right"
                self.sm.current = "main"

        if keycode[1] == 'enter':
            if self.sm.current == 'main':
                self.sm.screens[0].ids.password.text = ''
            if self.sm.current == 'info':
                self.sm.screens[2].ids.set_password.text = self.sm.screens[2].ids.set_password.text[:-1]
                self.sm.screens[2].validation()


def reset_app():
    df['password'] = 'None'
    df['team'] = 'None'
    df['mission_completed'] = 0
    df['mission'] = 'None'
    df['lose'] = False
    df['target_id'] = 'None'
    df.to_csv("data.csv", index=False)


def reset_mission():
    all_missions = np.array([])
    with open('missions.txt', encoding='utf-8') as file:
        for line in file:
            all_missions = np.append(all_missions, line)
    np.random.shuffle(all_missions)
    for player_id, row in df.iterrows():
        df.loc[player_id, 'mission'] = all_missions[0]
        all_missions = np.delete(all_missions, 0)
    df.to_csv('data.csv', index=False)


def reset_cycle():
    global cycle
    ids = np.array([k for k in range(NB_PLAYER)]).astype(str)
    np.random.shuffle(ids)
    with open('cycle.txt', 'w') as f:
        f.write('\n'.join(ids))

    load_cycle()
    for player_id, row in df.iterrows():
        df.loc[player_id, 'target_id'] = cycle[(np.where(cycle == player_id)[0][0] + 1) % NB_PLAYER]
    df.to_csv('data.csv', index=False)


def load_cycle():
    global cycle
    with open('cycle.txt', 'r') as f:
        for line in f:
            cycle = np.append(cycle, int(line))


if __name__ == '__main__':
    reset_app()
    reset_cycle()
    reset_mission()

    load_cycle()
    SGKApp().run()
