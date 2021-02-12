# import necessary classes
import math
import fileinput
import random
import time
from kivy.config import Config

from kivy.app import App
# kivy.require("1.10.1")
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.screenmanager import FadeTransition, CardTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.core.window import Window
Window.size = (570,600)

# settings panel
from kivy.config import ConfigParser
from kivy.uix.settings import SettingsWithSidebar
from RoguelikeSettings import logic

# displays "You Win!"
class WinLabel(Label):
    pass

# counter for number of drops collected
class DropLabel(Label):
    pass

# shows current level
class LevelLabel(Label):
    pass

# displays "Game Over"
class GameOverLabel(Label):
    pass

# button to go to settings screen
class SettingsButton(Button):
    def __init__(self, **kwargs):
        super(SettingsButton, self).__init__(**kwargs)

    def on_touch_up(self, touch):
        if (self.x <= touch.x <= self.right) and (self.y <= touch.y <= self.top):
            app.open_settings()

# manages current screen and transtions
class ScreenManagement(ScreenManager):
    def __init__(self, **kwargs):
        super(ScreenManagement, self).__init__(**kwargs)
        self.fade = FadeTransition()
        self.card = CardTransition()
        self.transition = self.fade

# menu screen
class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super(MenuScreen, self).__init__(**kwargs)
        self.name = "menu_screen"

# primary screen
class GameScreen(Screen):
    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        self.name = "game_screen"

# holds top menu + game screen
class MasterLayout(FloatLayout):
    def __init__(self, **kwargs):
        super(MasterLayout, self).__init__(**kwargs)

# game title
class TitleLabel(Label):
    def __init__(self, **kwargs):
        super(TitleLabel, self).__init__(**kwargs)

# starts game loop
class StartButton(Button):
    def __init__(self, **kwargs):
        super(StartButton, self).__init__(**kwargs)
        self.pressed = False

    # starts updating game
    def on_touch_up(self, touch):
        if (self.x <= touch.x <= self.right) and (self.y <= touch.y <= self.top) and self.pressed == False:
            root.ids["game"].toggle()
            self.pressed = True

# water drop collectable
class Drop(Image):
    def __init__(self, **kwargs):
        super(Drop, self).__init__(**kwargs)
        self.source = "drop.png"

    def set(self, position):
        self.pos = position

# player health indicator
class HealthBar(Image):
    def __init__(self, **kwargs):
        super(HealthBar, self).__init__(**kwargs)
        self.source = "2heart.png"
        self.pos = 0, Window.height*0.95-self.height

    def lose_health(self, health):
        if health == 4:
            self.source = "2heart.png"
        elif health == 3:
            self.source = "1.5heart.png"
        elif health == 2:
            self.source = "heart.png"
        elif health == 1:
            self.source = "halfheart.png"

# walls to build the level design with
class CollisionTile(Image):
    def __init__(self, **kwargs):
        super(CollisionTile, self).__init__(**kwargs)
        self.source = "wood.png"

    def set(self, x, y):
        self.size = Window.width/12, Window.height*0.95/12
        self.pos = x, y

    health = 4
    bullets = []

    # take damage from bullet widgets
    def take_damage(self, bullet):
        if bullet not in self.bullets and self.collide_widget(bullet):
            self.bullets.append(bullet)
            self.health -= 1
            return True
        else:
            return False

# playable character
class MainPlayer(Image):
    def __init__(self, **kwargs):
        super(MainPlayer, self).__init__(**kwargs)
        self.source = "watermelon1.png"

    # initialize values for player velocity
    velocity_x =  NumericProperty(0)
    velocity_y =  NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    health = 4

    # move player relative to current velocity and position
    def move(self):
        # keep player within window borders
        if self.top > Window.height * 0.95 - 55:
            self.top = Window.height * 0.95 - 55
        elif self.y < 0:
            self.y = 0
        elif self.right > Window.width:
            self.right = Window.width
        elif self.x < 0:
            self.x = 0
        # otherwise allow player movement
        else:
            self.pos = Vector(*self.velocity) + self.pos

# enemy that hones on player location
class HoningEnemy(Image):
    def __init__(self, **kwargs):
        super(HoningEnemy, self).__init__(**kwargs)
        self.source = "honingenemy.png"

    # initialize enemy velocity
    velocity_x =  NumericProperty(0)
    velocity_y =  NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    def set(self, x, y):
        self.pos = x, y

    # move bullet relative to current velocity and position
    def move(self):
        self.pos = Vector(*self.velocity) + self.pos

    health = 4
    bullets = []

    # follow the player
    def hone(self, player):
        dif_x = player.center_x - self.center_x
        dif_y = player.center_y - self.center_y

        dif_hyp = Vector(dif_x, dif_y).length()
        vel_scale = 0.9 / dif_hyp

        self.velocity_x = dif_x * vel_scale
        self.velocity_y = dif_y * vel_scale

    # take damage from bullet widgets
    def take_damage(self, bullet):
        if bullet not in self.bullets and self.collide_widget(bullet):
            self.bullets.append(bullet)
            self.health -= 1
            return True
        else:
            return False

# balls that player shoots
class PlayerBullet(Widget):
    # initialize values for bullet velocity
    velocity_x =  NumericProperty(0)
    velocity_y =  NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    # move bullet relative to current velocity and position
    def move(self):
        self.pos = Vector(*self.velocity) + self.pos

    # remove bullet if it exits the window
    def remove(self):
        if self.y >= Window.height or self.x >= Window.width or self.top <= 0 or self.right <= 0:
            return True
        else:
            return False

# main game functions
class RoguelikeGame(Widget):
    # bind to classes to keyboard listener and grab mouse
    def __init__(self, **kwargs):
        super(RoguelikeGame, self).__init__(**kwargs)
        Window.bind(on_key_up=self._keyup)
        Window.bind(on_key_down=self._keydown)
        #Window.grab_mouse()

        # initialize game clock and current level
        self.toggled = False
        self.game_clock = ObjectProperty(None)
        self.current_level = 1

        # set default keybinds for player movement
        self.updates_per_second = 60.0
        self.move_up = "w"
        self.up_code = 119
        self.move_down = "s"
        self.down_code = 115
        self.move_left = "a"
        self.left_code = 97
        self.move_right = "d"
        self.right_code = 100

        self.health_bar = HealthBar()


    # initialize player and droplabel opjects as well as lists to keep track of
    # bullets, tiles, enemies, and drops currently on screen
    player = ObjectProperty(None)
    bullets = []
    tiles = []
    enemies = []
    drops = []
    dropnum = 0
    startTime = 0
    droplabel = ObjectProperty(None)
    levellabel = ObjectProperty(None)


    def build_level(self, level_num):
        # add player widget
        self.player = MainPlayer()
        self.player.pos = Window.width/2 - 30, Window.height/2 - 30
        self.add_widget(self.player)
        # add drop counter widget and label
        drop = Drop()
        drop.set(Vector(150, Window.height*0.95-drop.height))
        self.add_widget(drop)
        self.droplabel = DropLabel()
        self.droplabel.pos = 125, Window.height*0.95-80
        self.add_widget(self.droplabel)
        self.droplabel.text = str(self.dropnum)
        # add level label
        self.levellabel = LevelLabel()
        self.levellabel.text = "Level " + str(self.current_level)
        self.levellabel.pos = 450, Window.height*0.95-80
        self.add_widget(self.levellabel)
        # update health bar
        self.health_bar.lose_health(self.player.health)
        self.add_widget(self.health_bar)


        # add widgets based on a level layout file
        with fileinput.input(files=r'C:\Users\Josh Poole\cs2021\projects\FinalProject\level' + str(level_num) + '.txt') as f:
            row = 11
            for line in f:
                col = 0
                for c in line:
                    # & represents a tile
                    if c == "&":
                        tile = CollisionTile()
                        self.add_widget(tile)
                        tile.set(Window.width/12*col, Window.height*0.95/12*row)
                        self.tiles.append(tile)
                    # $ represents an enemy
                    elif c == "$":
                        enemy = HoningEnemy()
                        self.add_widget(enemy)
                        enemy.set(Window.width/12*col, Window.height*0.95/12*row)
                        self.enemies.append(enemy)
                    col += 1
                row -= 1

    # shoot bullet from players current position with specific velocity
    def shoot_bullet(self, vel_x, vel_y):
        bullet = PlayerBullet()
        self.add_widget(bullet)
        bullet.velocity_x = vel_x
        bullet.velocity_y = vel_y
        bullet.center = self.player.center
        self.bullets.append(bullet)

    # adjust player velocity based on key input
    def _keydown(self, key, keycode, scancode, text, modifiers):
        v = 2.5
        if text == self.move_up:
            self.player.velocity_y = v
            if self.up_code != keycode:
                self.up_code = keycode
        elif text == self.move_down:
            self.player.velocity_y = -v
            if self.down_code != keycode:
                self.down_code = keycode
        elif text == self.move_left:
            self.player.velocity_x = -v
            if self.left_code != keycode:
                self.left_code = keycode
        elif text == self.move_right:
            self.player.velocity_x = v
            if self.right_code != keycode:
                self.right_code = keycode

    # halt player directional velocity based on which key is released
    def _keyup(self, key, keycode, scancode):
        if keycode == self.up_code or keycode == self.down_code:
            self.player.velocity_y = 0
        elif keycode == self.left_code or keycode == self.right_code:
            self.player.velocity_x = 0

    # determine bullet velocity (direction) based on touch input and call
    # shoot_bullet
    def on_touch_down(self, touch):
        dif_x = touch.x - self.player.center_x
        dif_y = touch.y - self.player.center_y

        dif_hyp = Vector(dif_x, dif_y).length()
        vel_scale = 10.0 / dif_hyp

        bullet_velocity_x = dif_x * vel_scale
        bullet_velocity_y = dif_y * vel_scale

        self.shoot_bullet(bullet_velocity_x, bullet_velocity_y)

    # update player, bullets, tiles, and enemies
    def update(self, dt):
        self.player.move()
        # load next level when all enemies are eliminated
        if self.enemies == []:
            self.nextLevel()
        # check if an enemy touches the player and update player health
        # accordingly
        for enemy in self.enemies:
            enemy.hone(self.player)
            enemy.move()
            endTime = time.time()
            if endTime - self.startTime > 3 and self.player.collide_widget(enemy):
                if self.player.health > 1:
                    self.player.health -= 1
                    self.health_bar.lose_health(self.player.health)
                    self.startTime = time.time()
                else:
                    self.gameOver()
        # check if the player collected a drop
        for drop in self.drops:
            if self.player.collide_widget(drop):
                self.drops.remove(drop)
                self.remove_widget(drop)
                self.dropnum += 1
                self.droplabel.text = str(self.dropnum)
        for bullet in self.bullets:
            bullet.move()
            # remove bullet if it goes off screen
            if bullet.remove():
                self.remove_widget(bullet)
                self.bullets.remove(bullet)
            else:
                checkTiles = True
                # check if an enemy collides with a bullet and adjest the health
                # of the enemy accordingly
                for enemy in self.enemies:
                    if enemy.take_damage(bullet):
                        self.remove_widget(bullet)
                        self.bullets.remove(bullet)
                        checkTiles = False
                        # remove enemy if health is 0
                        if enemy.health < 1:
                            self.remove_widget(enemy)
                            self.enemies.remove(enemy)
                # check if a bullet collides with a tile and adjust the health
                # of the tile accordingly
                if(checkTiles):
                    for tile in self.tiles:
                        if tile.take_damage(bullet):
                            self.remove_widget(bullet)
                            self.bullets.remove(bullet)
                            # remove tile if health is 0
                            if tile.health < 1:
                                self.remove_widget(tile)
                                self.tiles.remove(tile)
                                tilePos = tile.pos
                                drop = Drop()
                                drop.set(tilePos)
                                self.add_widget(drop)
                                self.drops.append(drop)

    # start or stop updating game
    def toggle(self):
        # if game is running, clear widgets and stop clock
        if self.toggled:
            self.toggled = False
            self.clear_widgets()
            self.game_clock.cancel()
        # if game is not running, start clock and build level
        else:
            self.game_clock = Clock.schedule_interval(self.update, 1.0 / self.updates_per_second)
            self.build_level(self.current_level)
            self.toggled = True

    # stop game clock then display "game over"
    def gameOver(self):
        self.toggle()
        self.clear_widgets()
        gameOver = GameOverLabel()
        gameOver.pos = 0.4*Window.width, 0.4*Window.height
        self.add_widget(gameOver)

    # stop game clock and display "you win"
    def youWin(self):
        self.toggle
        self.clear_widgets()
        winner = WinLabel()
        winner.pos = 0.4*Window.width, 0.4*Window.height
        self.add_widget(winner)

    # clear the screen and load the next level
    def nextLevel(self):
        if self.current_level == 3:
            self.youWin()
        else:
            self.toggle()
            #nextLevel = NextLevelLabel()
            #nextLevel.pos = 0.4*Window.width, 0.4*Window.height
            #self.add_widget(nextLevel)
            self.current_level += 1
            self.toggle()

# main application
class RoguelikeApp(App):
    def __init__(self, **kwargs):
        super(RoguelikeApp, self).__init__(**kwargs)

        # change settings
        self.settings_functions = {
            u'updates_per_second' : self.update_updates_per_second,
            u'move_up' : self.update_move_up,
            u'move_down' : self.update_move_down,
            u'move_left' : self.update_move_left,
            u'move_right' : self.update_move_right }

        global app
        app = self


    # initialize the application and update 60 times a second
    def build(self):
        self.root = ScreenManagement()
        self.root.current = "menu_screen"
        self.game = self.root.ids["game"]

        # settings panel
        self.settings_cls = SettingsWithSidebar
        self.use_kivy_settings = False

        # make global
        global root
        root = self.root
        return self.root

    # default settings values
    def build_config(self, config):
        config.setdefaults("logic", {
            "updates_per_second" : 60.0,
            "move_up" : "w",
            "move_down" : "s",
            "move_left" : "a",
            "move_right" : "d" })

    # adds settigns panel
    def build_settings(self, settings):
        settings.add_json_panel("Gameplay", self.config, data=logic)

    # calls corresponding function for changed setting
    def on_config_change(self, config, section, key, value):
        self.settings_functions.get(key, self.setting_not_found)(config, value)

    # in case setting is not there
    def setting_not_found(self, value, *args):
        print("Sorry " + str(value) + "setting not found")

    # changes update frequency
    def update_updates_per_second(self, config, new_updates_per_second):
        new_updates_per_second = float(new_updates_per_second)
        self.game.updates_per_second = new_updates_per_second

    # changes key for move up
    def update_move_up(self, config, new_move_up):
        self.game.move_up = new_move_up

    # changes key for move down
    def update_move_down(self, config, new_move_down):
        self.game.move_down = new_move_down

    # changes key for move left
    def update_move_left(self, config, new_move_left):
        self.game.move_left = new_move_left

    # changes key for move right
    def update_move_right(self, config, new_move_right):
        self.game.move_right = new_move_right

if __name__ == "__main__":
    RoguelikeApp().run()
