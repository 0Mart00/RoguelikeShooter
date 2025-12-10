from panda3d.core import NodePath, WindowProperties

class CameraManager:
    def __init__(self, base_app, target_node):
        self.base = base_app
        self.target = target_node # A célpont, amit követ (pl. játékos)
        
        # Paraméterek
        self.distance = 50
        self.height = 10
        self.sensitivity = 0.2 # Egér érzékenység
        
        # Pivot pont létrehozása (ez forog a játékos körül)
        self.pivot = NodePath("cam_pivot")
        self.pivot.reparentTo(self.base.render)
        
        # A valódi kamerát a pivothoz csatoljuk
        self.base.camera.reparentTo(self.pivot)
        self.base.camera.setPos(0, -self.distance, self.height)
        self.base.camera.lookAt(self.pivot)
        
        # Egér kezelés állapota
        self.cursor_locked = False
        self.lock_cursor() # Induláskor lockoljuk

    def update(self):
        """Minden frame-ben meghívandó: követés és forgatás."""
        # 1. Követjük a célpontot
        if self.target:
            self.pivot.setPos(self.target.getPos())

        # 2. Egér forgatás (csak ha lockolva van)
        if self.cursor_locked:
            self._handle_mouse_look()

    def _handle_mouse_look(self):
        win = self.base.win
        cx = win.getXSize() // 2
        cy = win.getYSize() // 2
        
        if not win.getPointer(0).getInWindow():
            return

        pointer = win.getPointer(0)
        x = pointer.getX()
        y = pointer.getY()
        
        if x != cx or y != cy:
            # Mennyit mozdult az egér a középhez képest?
            dx = x - cx
            dy = y - cy
            
            # Forgatás alkalmazása
            current_h = self.pivot.getH()
            current_p = self.pivot.getP()
            
            self.pivot.setH(current_h - dx * self.sensitivity)
            
            # Pitch (fel-le nézés) korlátozása
            new_p = current_p - dy * self.sensitivity
            new_p = max(-89, min(89, new_p))
            self.pivot.setP(new_p)
            
            # Egér visszarakása középre (Végtelen forgás trükk)
            win.movePointer(0, cx, cy)

    def lock_cursor(self):
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_absolute)
        self.base.win.requestProperties(props)
        self.cursor_locked = True
        
        # Azonnal középre tesszük
        cx = self.base.win.getXSize() // 2
        cy = self.base.win.getYSize() // 2
        self.base.win.movePointer(0, cx, cy)

    def unlock_cursor(self):
        props = WindowProperties()
        props.setCursorHidden(False)
        props.setMouseMode(WindowProperties.M_absolute)
        self.base.win.requestProperties(props)
        self.cursor_locked = False

    def get_heading(self):
        return self.pivot.getH()