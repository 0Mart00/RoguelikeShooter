import sys
from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight

# --- Modulok importálása a mappákból ---
try:
    # Terrain mappa
    from terrain.generator import generate_island
    from terrain.terrain import make_island_nodepath
    
    # Core mappa (Itt változott az útvonal!)
    from core.player import Player
    from core.camera_manager import CameraManager

except ImportError as e:
    print("HIBA: Hiányzó fájlok vagy modulok!")
    print(f"Részletek: {e}")
    print("Ellenőrizd, hogy léteznek-e a 'core' és 'terrain' mappák és bennük az __init__.py fájlok!")
    sys.exit()

class Game(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse() # Alapértelmezett kamera letiltása
        
        # 1. Környezet beállítása (Fények, Terrain)
        self.setup_environment()
        
        # 2. Játékos létrehozása
        self.player = Player(self.render, start_pos=(0, 0, 10))
        
        # 3. Kamera kezelő létrehozása
        self.cam_manager = CameraManager(self, self.player.node)
        
        # 4. Inputok beállítása
        self.keys = {"w": False, "s": False, "a": False, "d": False}
        self.setup_controls()

        # 5. Taskok indítása (Update loop)
        self.taskMgr.add(self.game_loop, "game_loop")

    def setup_environment(self):
        self.setBackgroundColor(0.5, 0.7, 0.9)

        # Fények
        alight = AmbientLight('alight')
        alight.setColor((0.4, 0.4, 0.4, 1))
        self.render.setLight(self.render.attachNewNode(alight))

        dlight = DirectionalLight('dlight')
        dlight.setColor((0.8, 0.8, 0.7, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(-45, -45, 0)
        self.render.setLight(dlnp)

        # Terrain
        print("Sziget generálása...")
        # Most már a terrain modulból hívjuk a függvényeket
        height_map = generate_island(size=129, height_scale=20.0, seed=42)
        self.terrain = make_island_nodepath(self, height_map, pos=(0, 0, -5))
        self.terrain.reparentTo(self.render)
        self.terrain.setColor(0.2, 0.6, 0.3, 1)

    def setup_controls(self):
        # Billentyű figyelés
        for key in self.keys:
            self.accept(key, self.set_key, [key, True])
            self.accept(key+"-up", self.set_key, [key, False])
        
        # Egér lock/unlock (Ctrl) és Kilépés (Esc)
        self.accept("control", self.cam_manager.unlock_cursor)
        self.accept("control-up", self.cam_manager.lock_cursor)
        self.accept("escape", self.userExit)

    def set_key(self, key, value):
        self.keys[key] = value

    def game_loop(self, task):
        dt = globalClock.getDt()
        
        # 1. Kamera frissítése
        self.cam_manager.update()
        
        # 2. Játékos frissítése
        cam_heading = self.cam_manager.get_heading()
        self.player.update_movement(dt, self.keys, cam_heading)
        
        return task.cont

if __name__ == "__main__":
    game = Game()
    game.run()