from direct.gui.DirectGui import *
from panda3d.core import TextNode, WindowProperties

# --- UI Konstansok (Stílus) ---
BTN_WIDTH = 0.3
BTN_HEIGHT = 0.06
TEXT_COLOR = (1, 1, 1, 1)
LABEL_COLOR = (0.9, 0.9, 0.9, 1)

class SettingsMenu:
    """
    Ez az osztály kezeli a beállítások ablakot és a játék paramétereinek módosítását.
    """
    def __init__(self, main_app):
        self.main_app = main_app  # Referencia a fő alkalmazásra (hogy vissza tudjunk lépni)
        self.base = main_app      # ShowBase referencia
        
        # Konténer létrehozása (alapból rejtve van)
        self.frame = DirectFrame(
            frameSize=(-1.2, 1.2, -0.9, 0.9),
            frameColor=(0.1, 0.1, 0.1, 0.9), # Sötét, majdnem átlátszatlan háttér
            parent=self.base.aspect2d
        )
        self.frame.hide()

        self.setup_ui()

    def show(self):
        """Megjeleníti a beállításokat."""
        self.frame.show()

    def hide(self):
        """Elrejti a beállításokat."""
        self.frame.hide()

    def setup_ui(self):
        """Létrehozza az összes csúszkát, gombot és feliratot."""
        
        # --- Cím ---
        DirectLabel(
            text="BEÁLLÍTÁSOK",
            scale=0.12,
            pos=(0, 0, 0.75),
            text_fg=TEXT_COLOR,
            frameColor=(0, 0, 0, 0),
            parent=self.frame
        )

        # --- 1. Szekció: Megjelenítés (Bal oldal) ---
        start_y = 0.5
        col_1_x = -0.5

        # Felirat: Kép
        DirectLabel(text="MEGJELENÍTÉS", scale=0.08, pos=(col_1_x, 0, start_y), 
                    text_fg=(1, 1, 0.5, 1), frameColor=(0,0,0,0), parent=self.frame)

        # Felbontás választó (Dropdown)
        DirectLabel(text="Felbontás:", scale=0.05, pos=(col_1_x, 0, start_y - 0.15),
                    text_align=TextNode.ALeft, text_fg=LABEL_COLOR, frameColor=(0,0,0,0), parent=self.frame)
        
        self.res_menu = DirectOptionMenu(
            text="1280x720", 
            scale=0.05, 
            items=["1280x720", "1920x1080", "800x600"],
            initialitem=0,
            highlightColor=(0.65, 0.65, 0.65, 1),
            command=self.set_resolution,
            pos=(col_1_x + 0.3, 0, start_y - 0.15),
            parent=self.frame
        )

        # Teljes képernyő (Checkbox)
        self.fullscreen_btn = DirectCheckButton(
            text="Teljes képernyő",
            scale=0.05,
            pos=(col_1_x, 0, start_y - 0.3),
            command=self.toggle_fullscreen,
            text_fg=LABEL_COLOR,
            indicator_text_fg=(1,1,1,1), # A pipa színe
            boxBorder=0,
            parent=self.frame
        )

        # --- 2. Szekció: Hang és Játékmenet (Jobb oldal) ---
        col_2_x = 0.5
        
        # Felirat: Audio
        DirectLabel(text="HANG & JÁTÉK", scale=0.08, pos=(col_2_x, 0, start_y), 
                    text_fg=(1, 1, 0.5, 1), frameColor=(0,0,0,0), parent=self.frame)

        # Hangerő Csúszka (Slider)
        DirectLabel(text="Fő Hangerő:", scale=0.05, pos=(col_2_x - 0.3, 0, start_y - 0.15),
                    text_align=TextNode.ALeft, text_fg=LABEL_COLOR, frameColor=(0,0,0,0), parent=self.frame)
        
        self.vol_slider = DirectSlider(
            range=(0, 100),
            value=50,
            pageSize=10,
            scale=0.3, # Szélesség
            pos=(col_2_x + 0.2, 0, start_y - 0.14),
            command=self.set_volume,
            parent=self.frame
        )

        # Látószög (FOV) Slider
        DirectLabel(text="Látószög (FOV):", scale=0.05, pos=(col_2_x - 0.3, 0, start_y - 0.3),
                    text_align=TextNode.ALeft, text_fg=LABEL_COLOR, frameColor=(0,0,0,0), parent=self.frame)

        self.fov_slider = DirectSlider(
            range=(60, 120),
            value=90,
            pageSize=5,
            scale=0.3,
            pos=(col_2_x + 0.2, 0, start_y - 0.29),
            command=self.set_fov,
            parent=self.frame
        )
        
        # --- Vissza Gomb (Alul) ---
        DirectButton(
            text="VISSZA A MENÜBE",
            scale=1.0,
            text_scale=0.06,
            pos=(0, 0, -0.7),
            frameSize=(-0.3, 0.3, -0.06, 0.06),
            command=self.go_back,
            parent=self.frame,
            text_fg=(1,1,1,1),
            frameColor=((0.6, 0.2, 0.2, 1), (0.8, 0.3, 0.3, 1), (0.4, 0.1, 0.1, 1))
        )

    # --- Callback Függvények (Működés) ---

    def set_resolution(self, arg):
        """Beállítja a képernyő felbontását."""
        print(f"[Settings] Felbontás váltása: {arg}")
        width, height = map(int, arg.split('x'))
        
        props = WindowProperties()
        props.setSize(width, height)
        self.base.win.requestProperties(props)

    def toggle_fullscreen(self, status):
        """Ki/Be kapcsolja a teljes képernyőt."""
        print(f"[Settings] Teljes képernyő: {status}")
        props = WindowProperties()
        props.setFullscreen(status)
        self.base.win.requestProperties(props)

    def set_volume(self):
        """Hangerő beállítása."""
        # A Slider értéke a ['value'] kulccsal érhető el
        vol = int(self.vol_slider['value'])
        print(f"[Settings] Hangerő: {vol}%")
        # Itt hívnád meg a Panda3D audio managerét:
        # base.musicManager.setVolume(vol / 100.0)

    def set_fov(self):
        """Kamera látószög (FOV) beállítása."""
        fov = int(self.fov_slider['value'])
        print(f"[Settings] FOV: {fov}")
        self.base.camLens.setFov(fov)

    def go_back(self):
        """Visszatérés a főmenübe."""
        self.hide()
        # Visszahívjuk a főmenü megjelenítő függvényét
        self.main_app.menu_container.show()