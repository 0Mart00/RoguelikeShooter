from panda3d.core import (
    NodePath, WindowProperties, Vec3, 
    CollisionTraverser, CollisionHandlerQueue, 
    CollisionSegment, CollisionNode, BitMask32
)

class CameraManager:
    def __init__(self, base_app, target_node):
        self.base = base_app
        self.target = target_node # A célpont, amit követ (pl. játékos)
        
        # Paraméterek
        self.distance = 25.0
        self.height = 10.0
        self.sensitivity = 0.2
        self.min_distance = 2.0 # Ennél közelebb nem jöhet
        
        # Pivot pont (ez forog a játékos körül)
        self.pivot = NodePath("cam_pivot")
        self.pivot.reparentTo(self.base.render)
        
        # A valódi kamerát a pivothoz csatoljuk
        self.base.camera.reparentTo(self.pivot)
        # Kezdeti pozíció beállítása
        self.base.camera.setPos(0, -self.distance, self.height)
        self.base.camera.lookAt(self.pivot)
        
        # --- ÜTKÖZÉSVIZSGÁLAT (Anti-Clip) ---
        self.cTrav = CollisionTraverser()
        self.cQueue = CollisionHandlerQueue()
        
        # Egy szakaszt (Segment) húzunk a Pivot és a Kamera közé
        # A pontokat dinamikusan frissítjük az update-ben
        # JAVÍTÁS: A pontok nem lehetnek egyformák (AssertionError elkerülése)
        self.cam_ray = CollisionSegment(0, 0, 0, 0, 0, 1)
        self.cam_ray_node = CollisionNode('cam_ray')
        self.cam_ray_node.addSolid(self.cam_ray)
        
        # Csak a tereppel (Bit 1) akarunk ütközni, a játékossal (Bit 2) nem
        self.cam_ray_node.setFromCollideMask(BitMask32.bit(1))
        self.cam_ray_node.setIntoCollideMask(BitMask32.allOff())
        
        # A sugarat a pivothoz csatoljuk
        self.cam_ray_np = self.pivot.attachNewNode(self.cam_ray_node)
        self.cTrav.addCollider(self.cam_ray_np, self.cQueue)
        
        # Egér kezelés
        self.cursor_locked = False
        self.lock_cursor()

    def update(self):
        """Minden frame-ben meghívandó."""
        # 1. Követjük a célpontot
        if self.target:
            # A pivot a játékos feje magasságában legyen (pl. +2 Z), ne a talpánál
            target_pos = self.target.getPos() + Vec3(0, 0, 2.0)
            self.pivot.setPos(target_pos)

        # 2. Egér forgatás
        if self.cursor_locked:
            self._handle_mouse_look()
            
        # 3. Kamera ütközésvizsgálat (Spring Arm)
        self._handle_camera_collision()

    def _handle_camera_collision(self):
        # Az ideális pozíció (ha nincs fal):
        ideal_pos = Vec3(0, -self.distance, self.height)
        
        # A sugár kezdőpontja (Pivot közepe)
        origin = Vec3(0, 0, 0)
        
        # Beállítjuk a sugarat a Pivot koordinátarendszerében
        self.cam_ray.setPointA(origin)
        self.cam_ray.setPointB(ideal_pos)
        
        # Vizsgálat futtatása
        self.cTrav.traverse(self.base.render)
        
        if self.cQueue.getNumEntries() > 0:
            self.cQueue.sortEntries()
            entry = self.cQueue.getEntry(0)
            
            # A találat pontja (lokálisan a pivotkoz képest)
            hit_pos = entry.getSurfacePoint(self.pivot)
            
            # Kicsit húzzuk előrébb a kamerát a találati ponttól, 
            # hogy ne legyen pont a falban (0.9-es szorzó)
            collision_dist = hit_pos.length()
            
            # Ne engedjük túl közelre se
            if collision_dist < self.min_distance:
                collision_dist = self.min_distance
                
            # Az irányvektor az origótól az ideális pozíció felé
            direction = ideal_pos / ideal_pos.length()
            
            # Beállítjuk az új pozíciót
            self.base.camera.setPos(direction * (collision_dist * 0.9))
            
        else:
            # Ha nincs ütközés, mehet az ideális helyre
            self.base.camera.setPos(ideal_pos)

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
            dx = x - cx
            dy = y - cy
            
            current_h = self.pivot.getH()
            current_p = self.pivot.getP()
            
            self.pivot.setH(current_h - dx * self.sensitivity)
            
            new_p = current_p - dy * self.sensitivity
            new_p = max(-89, min(89, new_p))
            self.pivot.setP(new_p)
            
            win.movePointer(0, cx, cy)

    def lock_cursor(self):
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_absolute)
        self.base.win.requestProperties(props)
        self.cursor_locked = True
        
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