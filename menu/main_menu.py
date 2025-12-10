import sys
import logging
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import *
from panda3d.core import (
    TextNode, 
    LVector3f, 
    WindowProperties
)

# Importáljuk az új Settings osztályt
from settings_menu import SettingsMenu
# Importáljuk a színeket a configból
from config.colors import Colors

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# UI Méretezés
BTN_WIDTH = 0.4
BTN_HEIGHT = 0.06
BTN_SPACING = 0.15

class MainMenu(ShowBase):
    """
    Főmenü osztály, amely a Panda3D ShowBase-ből örököl.
    """
    def __init__(self):
        ShowBase.__init__(self)

        # Ablak beállítása
        self.props = WindowProperties()
        self.props.setTitle("Panda3D Játék Főmenü - Javított Hitbox")
        self.props.set_size(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.win.requestProperties(self.props)

        # Háttérszín beállítása a Colors osztályból
        self.setBackgroundColor(Colors.BACKGROUND_MAIN)
        
        self.menu_container = None
        
        # Settings menü
        self.settings_menu = SettingsMenu(self)
        
        self.setup_main_menu()
        
        logging.info("A főmenü sikeresen elindult.")

    def setup_main_menu(self):
        """Létrehozza a főmenü összes gombját és címét."""
        
        if self.menu_container:
            self.menu_container.destroy()
        
        self.menu_container = DirectFrame(frameSize=(-1, 1, -1, 1),
                                          frameColor=Colors.TRANSPARENT,
                                          parent=self.aspect2d)
        
        # Cím
        self.title = DirectLabel(
            text="JÁTÉK CÍM",
            scale=0.15, 
            pos=(0, 0, 0.7),
            text_fg=Colors.TEXT_DEFAULT,
            text_shadow=Colors.TEXT_SHADOW,
            frameColor=Colors.TRANSPARENT,
            parent=self.menu_container
        )

        menu_items = [
            ("Single Player", self.start_single_player),
            ("Multiplayer", self.show_multiplayer_settings),
            ("Settings", self.show_settings),
            ("Achievement", self.show_achievements),
            ("Quit", self.quit_game)
        ]
        
        start_y = 0.4
        
        for i, (text, command) in enumerate(menu_items):
            btn_y = start_y - (i * BTN_SPACING)
            self.create_button(text, command, (0, 0, btn_y), self.menu_container)

        logging.info("Főmenü gombjai beállítva.")

    def create_button(self, text, command, pos, parent):
        """Segédfüggvény egy egységes gomb létrehozására."""
        return DirectButton(
            text=text,
            scale=1.0, 
            text_scale=0.07,
            pos=pos,
            frameSize=(-BTN_WIDTH, BTN_WIDTH, -BTN_HEIGHT, BTN_HEIGHT),
            borderWidth=(0.005, 0.005),
            command=command,
            parent=parent,
            relief=DGG.FLAT,
            text_align=TextNode.ACenter,
            
            # Színek használata a Colors osztályból
            text_fg = Colors.TEXT_DEFAULT, 
            frameColor=(Colors.BTN_MAIN_NORMAL, 
                        Colors.BTN_MAIN_HOVER, 
                        Colors.BTN_MAIN_CLICK)
        )

    # --- Menüparancsok ---

    def start_single_player(self):
        logging.info("=> Egyjátékos Mód indítása...")

    def show_multiplayer_settings(self):
        logging.info("=> Többjátékos Menü betöltése...")

    def show_settings(self):
        logging.info("=> Beállítások Menü betöltése...")
        self.menu_container.hide()
        self.settings_menu.show()

    def show_achievements(self):
        logging.info("=> Eredmények (Achievements) Menü betöltése...")

    def quit_game(self):
        logging.info("=> Kilépés a játékból.")
        self.userExit()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s | PANDA3D | %(levelname)s | %(message)s',
                        datefmt='%H:%M:%S')
    
    app = MainMenu()
    app.run()