from direct.gui.DirectGui import *
from panda3d.core import TextNode, WindowProperties

# Importáljuk a színeket a config mappából
from config.colors import Colors

# --- UI Konstansok (Méretek) ---
BTN_WIDTH = 0.3
BTN_HEIGHT = 0.06

class SettingsMenu:
    """
    Ez az osztály kezeli a beállítások ablakot és a játék paramétereinek módosítását.
    """
    def __init__(self, main_app):
        self.main_app = main_app  # Referencia a fő alkalmazásra
        self.base = main_app      # ShowBase referencia
        
        # Konténer létrehozása
        self.frame = DirectFrame(
            frameSize=(-1.2, 1.2, -0.9, 0.9),
            frameColor=Colors.PANEL_DARK, # Szín használata
            parent=self.base.aspect2d
        )
        self.frame.hide()

        self.setup_ui()

    def show(self):
        self.frame.show()

    def hide(self):
        self.frame.hide()

    def setup_ui(self):
        """Létrehozza az összes csúszkát, gombot és feliratot."""
        
        # --- Cím ---
        DirectLabel(
            text="BEÁLLÍTÁSOK",
            scale=0.12,
            pos=(0, 0, 0.75),
            text_fg=Colors.TEXT_DEFAULT,
            frameColor=Colors.TRANSPARENT,
            parent=self.frame
        )

        # --- 1. Szekció: Megjelenítés (Bal oldal) ---
        start_y = 0.5
        col_1_x = -0.5

        # Felirat: Kép
        DirectLabel(text="MEGJELENÍTÉS", scale=0.08, pos=(col_1_x, 0, start_y), 
                    text_fg=Colors.TEXT_HIGHLIGHT, frameColor=Colors.TRANSPARENT, parent=self.frame)

        # Felbontás választó (Dropdown)
        DirectLabel(text="Felbontás:", scale=0.05, pos=(col_1_x, 0, start_y - 0.15),
                    text_align=TextNode.ALeft, text_fg=Colors.TEXT_LABEL, frameColor=Colors.TRANSPARENT, parent=self.frame)
        
        self.res_menu = DirectOptionMenu(
            text="1280x720", 
            scale=0.05, 
            items=["1280x720", "1920x1080", "800x600"],
            initialitem=0,
            highlightColor=Colors.DROPDOWN_HIGHLIGHT,
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
            text_fg=Colors.TEXT_LABEL,
            indicator_text_fg=Colors.CHECKBOX_TICK,
            boxBorder=0,
            parent=self.frame
        )

        # --- 2. Szekció: Hang és Játékmenet (Jobb oldal) ---
        col_2_x = 0.5
        
        # Felirat: Audio
        DirectLabel(text="HANG & JÁTÉK", scale=0.08, pos=(col_2_x, 0, start_y), 
                    text_fg=Colors.TEXT_HIGHLIGHT, frameColor=Colors.TRANSPARENT, parent=self.frame)

        # Hangerő Csúszka (Slider)
        DirectLabel(text="Fő Hangerő:", scale=0.05, pos=(col_2_x - 0.3, 0, start_y - 0.15),
                    text_align=TextNode.ALeft, text_fg=Colors.TEXT_LABEL, frameColor=Colors.TRANSPARENT, parent=self.frame)
        
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
                    text_align=TextNode.ALeft, text_fg=Colors.TEXT_LABEL, frameColor=Colors.TRANSPARENT, parent=self.frame)

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
            text_fg=Colors.WHITE,
            frameColor=(Colors.BTN_RED_NORMAL, Colors.BTN_RED_HOVER, Colors.BTN_RED_CLICK)
        )

    # --- Callback Függvények ---

    def set_resolution(self, arg):
        print(f"[Settings] Felbontás váltása: {arg}")
        width, height = map(int, arg.split('x'))
        props = WindowProperties()
        props.setSize(width, height)
        self.base.win.requestProperties(props)

    def toggle_fullscreen(self, status):
        print(f"[Settings] Teljes képernyő: {status}")
        props = WindowProperties()
        props.setFullscreen(status)
        self.base.win.requestProperties(props)

    def set_volume(self):
        vol = int(self.vol_slider['value'])
        print(f"[Settings] Hangerő: {vol}%")

    def set_fov(self):
        fov = int(self.fov_slider['value'])
        print(f"[Settings] FOV: {fov}")
        self.base.camLens.setFov(fov)

    def go_back(self):
        self.hide()
        self.main_app.menu_container.show()