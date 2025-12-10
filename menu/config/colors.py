class Colors:
    """
    Központosított színkezelés a játék UI elemeihez.
    Formátum: (R, G, B, Alpha)
    """
    
    # --- Általános ---
    WHITE = (1, 1, 1, 1)
    BLACK = (0, 0, 0, 1)
    TRANSPARENT = (0, 0, 0, 0)
    
    # --- Hátterek ---
    BACKGROUND_MAIN = (0.2, 0.2, 0.6)        # Főmenü háttérkék
    PANEL_DARK = (0.1, 0.1, 0.1, 0.9)        # Beállítások panel sötét háttere
    
    # --- Szövegek ---
    TEXT_DEFAULT = (1, 1, 1, 1)              # Alap fehér szöveg
    TEXT_SHADOW = (0, 0, 0, 1)               # Szöveg árnyék
    TEXT_LABEL = (0.9, 0.9, 0.9, 1)          # Kicsit halványabb címkék
    TEXT_HIGHLIGHT = (1, 1, 0.5, 1)          # Sárgás kiemelés (pl. szekció címek)
    
    # --- Főmenü Gombok (Kék stílus) ---
    BTN_MAIN_NORMAL = (0.2, 0.2, 0.4, 0.9)   # Sötétkék
    BTN_MAIN_HOVER = (0.4, 0.4, 0.7, 0.9)    # Világosabb kék
    BTN_MAIN_CLICK = (0.2, 0.6, 0.2, 0.9)    # Zöldes (kattintáskor)
    
    # --- "Vissza" / Veszélyes Gombok (Piros stílus) ---
    BTN_RED_NORMAL = (0.6, 0.2, 0.2, 1)
    BTN_RED_HOVER = (0.8, 0.3, 0.3, 1)
    BTN_RED_CLICK = (0.4, 0.1, 0.1, 1)
    
    # --- UI Elemek ---
    DROPDOWN_HIGHLIGHT = (0.65, 0.65, 0.65, 1)
    CHECKBOX_TICK = (1, 1, 1, 1)