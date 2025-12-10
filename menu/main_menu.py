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

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# JAVÍTÁS: Mivel a gomb scale-jét 1.0-ra állítjuk (hogy a hitbox pontos legyen),
# ezeket az értékeket a képernyő arányaihoz igazítjuk (-1 és 1 között).
BTN_WIDTH = 0.4   # A gomb fél szélessége (tehát 0.8 széles lesz)
BTN_HEIGHT = 0.06 # A gomb fél magassága
BTN_SPACING = 0.15 # Távolság a gombok között

class MainMenu(ShowBase):
    """
    Főmenü osztály, amely a Panda3D ShowBase-ből örököl.
    Ez kezeli az ablakot, a ciklust és a 2D menü elemeket.
    """
    def __init__(self):
        ShowBase.__init__(self)

        # Ablak beállítása és cím
        self.props = WindowProperties()
        self.props.setTitle("Panda3D Játék Főmenü - Javított Hitbox")
        self.props.set_size(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.win.requestProperties(self.props)

        # Háttérszín beállítása (kék)
        self.setBackgroundColor(0.2, 0.2, 0.6)
        
        self.menu_container = None
        
        # Settings menü példányosítása (átadjuk a 'self'-et referenciaként)
        self.settings_menu = SettingsMenu(self)
        
        # 1. Főmenü megjelenítése
        self.setup_main_menu()
        
        logging.info("A főmenü sikeresen elindult.")

    def setup_main_menu(self):
        """Létrehozza a főmenü összes gombját és címét."""
        
        if self.menu_container:
            self.menu_container.destroy()
        
        # A konténer skáláját alaphelyzetben hagyjuk
        self.menu_container = DirectFrame(frameSize=(-1, 1, -1, 1),
                                          frameColor=(0, 0, 0, 0),
                                          parent=self.aspect2d)
        
        # Cím
        self.title = DirectLabel(
            text="JÁTÉK CÍM",
            scale=0.15, # Szöveg méret
            pos=(0, 0, 0.7),
            text_fg=(1, 1, 1, 1), # Fehér szöveg
            text_shadow=(0, 0, 0, 1),
            frameColor=(0, 0, 0, 0), # Átlátszó háttér a címnek
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
        """
        Segédfüggvény egy egységes gomb létrehozására.
        JAVÍTÁS: A scale 1.0, a text_scale külön van kezelve.
        """
        return DirectButton(
            text=text,
            
            # JAVÍTÁS: A scale-t 1-re állítjuk, hogy a frameSize koordináták
            # valós képernyő-koordináták legyenek.
            scale=1.0, 
            
            # JAVÍTÁS: A szöveget külön méretezzük a gombon belül
            text_scale=0.07,
            
            pos=pos,
            
            # Hitbox és vizuális méret (xmin, xmax, ymin, ymax)
            frameSize=(-BTN_WIDTH, BTN_WIDTH, -BTN_HEIGHT, BTN_HEIGHT),
            borderWidth=(0.005, 0.005),
            
            command=command,
            parent=parent,
            relief=DGG.FLAT,
            
            # Szöveg igazítása középre
            text_align=TextNode.ACenter,
            
            # Text szín
            text_fg = (1, 1, 1, 1), 
                       
            # Frame színek állapotokhoz (Normal, Hover, Click, Disabled)
            # 1. Normal: Sötétkék
            # 2. Hover: Világosabb kék
            # 3. Click: Zöld (hogy lássuk a kattintást)
            frameColor=( (0.2, 0.2, 0.4, 0.9), 
                         (0.4, 0.4, 0.7, 0.9), 
                         (0.2, 0.6, 0.2, 0.9) )
        )
        

    # --- Menüparancsok (Játéklogika) ---

    def start_single_player(self):
        logging.info("=> Egyjátékos Mód indítása...")
        # Példa: gomb elrejtése vagy játék indítása
        # self.menu_container.hide()

    def show_multiplayer_settings(self):
        logging.info("=> Többjátékos Menü betöltése...")

    def show_settings(self):
        """Beállítások menü megjelenítése."""
        logging.info("=> Beállítások Menü betöltése...")
        # 1. Elrejtjük a főmenü konténert
        self.menu_container.hide()
        # 2. Megjelenítjük a settings ablakot
        self.settings_menu.show()

    def show_achievements(self):
        logging.info("=> Eredmények (Achievements) Menü betöltése...")

    def quit_game(self):
        logging.info("=> Kilépés a játékból.")
        self.userExit()

# --- Futtatás ---

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s | PANDA3D | %(levelname)s | %(message)s',
                        datefmt='%H:%M:%S')
    
    app = MainMenu()
    app.run()