from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    NodePath, Vec3, WindowProperties, GeomNode, 
    GeomVertexFormat, GeomVertexData, GeomVertexWriter, 
    GeomTriangles, Geom, AmbientLight, DirectionalLight
)
from math import sin, cos, radians

# --- Importáljuk a terrain modulokat ---
try:
    from terrain.generator import generate_island
    from terrain.terrain import make_island_nodepath
except ImportError as e:
    print("HIBA: Nem sikerült importálni a terrain modulokat!")
    print(f"Részletek: {e}")
    print("Biztosítsd, hogy a 'numpy', 'noise' és 'scipy' telepítve van: pip install numpy noise scipy")
    exit()

class Game(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse()
        
        # --- Beállítások ---
        self.setBackgroundColor(0.5, 0.7, 0.9) # Égbolt kék háttér

        # --- Kamera paraméterek ---
        self.cam_distance = 25 # Kicsit távolabb, hogy lássuk a szigetet
        self.cam_height = 10
        self.cam_speed = 50
        self.prev_mouse_pos = None

        # --- Fények (Hogy látszódjon a terrain domborzata!) ---
        # 1. Ambient (szórt) fény
        alight = AmbientLight('alight')
        alight.setColor((0.4, 0.4, 0.4, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)

        # 2. Directional (nap) fény
        dlight = DirectionalLight('dlight')
        dlight.setColor((0.8, 0.8, 0.7, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(-45, -45, 0) # Nap állása
        self.render.setLight(dlnp)

        # --- Player kocka ---
        self.player = self.make_box(2.0)
        self.player.reparentTo(self.render)
        self.player.setPos(0, 0, 10) # Magasabbra tesszük, hogy ráessen a szigetre (ha lenne fizika)
        self.player.setColor(1, 0, 0, 1) # Piros játékos

        # --- TERRAIN GENERÁLÁS ---
        print("Sziget generálása folyamatban...")
        # 1. Magasságtérkép generálása (129x129 felbontás)
        height_map = generate_island(size=129, height_scale=20.0, seed=42)
        
        # 2. Geometria létrehozása és lerakása
        self.terrain = make_island_nodepath(
            self, 
            height_map, 
            pos=(0, 0, -5),   # Kicsit lejjebb toljuk
            scale=(1, 1, 1)   # X, Y skálázás (pl. 2,2-vel ritkább lenne a rács)
        )
        self.terrain.reparentTo(self.render)
        self.terrain.setColor(0.2, 0.6, 0.3, 1) # Zöldes alapszín
        print("Kész!")

        # --- Pivot a kamera számára ---
        self.cam_pivot = NodePath("cam_pivot")
        self.cam_pivot.reparentTo(self.render)
        self.camera.reparentTo(self.cam_pivot)
        self.camera.setPos(0, -self.cam_distance, self.cam_height)
        self.camera.lookAt(self.cam_pivot)

        # --- Input kezelés (WASD) ---
        self.keys = {"w":False,"s":False,"a":False,"d":False}
        for key in self.keys:
            self.accept(key, self.set_key, [key, True])
            self.accept(key+"-up", self.set_key, [key, False])

        # Kurzor lock
        self.cursor_locked = True
        self.lock_cursor()
        self.accept("control", self.unlock_cursor)
        self.accept("control-up", self.lock_cursor)
        self.accept("escape", self.userExit)

        # Task-ok
        self.taskMgr.add(self.update_player, "update_player")
        self.taskMgr.add(self.update_camera, "update_camera")

    # -----------------------------
    # Kurzor lock/unlock
    # -----------------------------
    def lock_cursor(self):
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_confined)
        self.win.requestProperties(props)
        self.cursor_locked = True
        self.prev_mouse_pos = None

    def unlock_cursor(self):
        props = WindowProperties()
        props.setCursorHidden(False)
        props.setMouseMode(WindowProperties.M_absolute)
        self.win.requestProperties(props)
        self.cursor_locked = False

    # -----------------------------
    # Egérrel forgatható kamera
    # -----------------------------
    def update_camera(self, task):
        if self.cursor_locked and self.mouseWatcherNode.hasMouse():
            x = self.mouseWatcherNode.getMouseX()
            y = self.mouseWatcherNode.getMouseY()
            if self.prev_mouse_pos is not None:
                dx = x - self.prev_mouse_pos[0]
                dy = y - self.prev_mouse_pos[1]

                # Delta alapján frissítés
                new_h = self.cam_pivot.getH() - dx * self.cam_speed
                new_p = self.cam_pivot.getP() + dy * self.cam_speed

                # Pitch korlátozása
                new_p = max(-89, min(89, new_p))

                self.cam_pivot.setH(new_h)
                self.cam_pivot.setP(new_p)

            self.prev_mouse_pos = (x, y)

        # Pivot követi a játékost
        self.cam_pivot.setPos(self.player.getPos())
        return task.cont

    # -----------------------------
    # WASD játékos mozgatás
    # -----------------------------
    def set_key(self, key, value):
        self.keys[key] = value

    def update_player(self, task):
        dt = globalClock.getDt()
        speed = 10 # Kicsit gyorsabb mozgás a szigeten
        pos = self.player.getPos()
        direction = Vec3(0,0,0)
        
        # Mozgás irány a kamera nézete alapján
        if self.keys["w"]: direction.y += 1
        if self.keys["s"]: direction.y -= 1
        if self.keys["a"]: direction.x -= 1
        if self.keys["d"]: direction.x += 1

        if direction.length() > 0:
            direction.normalize()
            # Pivot H alapján forgatás a kamera irányába
            h = radians(self.cam_pivot.getH())
            rotated_dir = Vec3(
                direction.x * cos(h) - direction.y * sin(h),
                direction.x * sin(h) + direction.y * cos(h),
                0
            )
            pos += rotated_dir * speed * dt
            self.player.setPos(pos)

        return task.cont

    # -----------------------------
    # Kocka létrehozása
    # -----------------------------
    def make_box(self, size):
        fmt = GeomVertexFormat.getV3n3()
        vdata = GeomVertexData("cube", fmt, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")

        hs = size/2
        points = [
            (-hs,-hs,-hs), (hs,-hs,-hs), (hs,hs,-hs), (-hs,hs,-hs),
            (-hs,-hs,hs), (hs,-hs,hs), (hs,hs,hs), (-hs,hs,hs)
        ]
        # Box vertexek
        for p in points:
            vertex.addData3(*p)
            normal.addData3(0,0,1) # Egyszerűsített normál (nem tökéletes kocka shading, de elég)

        tris = GeomTriangles(Geom.UHStatic)
        # Figyelem: A box vertex indexelése a fenti listában egyszerűsített,
        # A helyes kockához laponként kellene duplikálni a vertexeket a normálok miatt.
        # De a teszthez ez a topológia megfelel.
        faces = [
            (0,1,2,3), (4,5,6,7), (0,1,5,4),
            (2,3,7,6), (0,3,7,4), (1,2,6,5)
        ]
        for f in faces:
            tris.addVertices(f[0],f[1],f[2])
            tris.addVertices(f[0],f[2],f[3])

        geom = Geom(vdata)
        geom.addPrimitive(tris)
        node = GeomNode("cube")
        node.addGeom(geom)
        return NodePath(node)

if __name__ == "__main__":
    game = Game()
    game.run()