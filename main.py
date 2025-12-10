import sys
from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight

# --- Modulok importálása a mappákból ---
try:
    # 1. Terrain modulok
    from terrain.generator import generate_island
    from terrain.terrain import make_island_nodepath, make_radial_island_nodepath
    
    # 2. Core modulok
    from core.player import Player
    from core.camera_manager import CameraManager
    # ÚJ: Importáljuk a fizikát
    from core.physics import PhysicsManager

except ImportError as e:
    print("HIBA: Hiányzó fájlok vagy modulok!")
    print(f"Részletek: {e}")
    print("Ellenőrizd, hogy léteznek-e a 'core' és 'terrain' mappák!")
    sys.exit()

class Game(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse() # Alapértelmezett kamera letiltása
        
        # 1. Környezet beállítása
        self.setup_environment()
        
        # 2. Terrain generálás
        self.setup_terrain()

        # 3. Játékos létrehozása (Magasról indítjuk: Z=50)
        self.player = Player(self.render, start_pos=(0, 0, 50))
        
        # 4. Kamera kezelő
        self.cam_manager = CameraManager(self, self.player.node)
        
        # 5. FIZIKA LÉTREHOZÁSA ÉS BEÁLLÍTÁSA
        self.physics = PhysicsManager(self)
        # Összekötjük a játékost és a terepet
        self.physics.setup_collision(self.player, self.terrain)
        
        # 6. Inputok beállítása
        self.keys = {"w": False, "s": False, "a": False, "d": False}
        self.setup_controls()

        # 7. Taskok indítása
        self.taskMgr.add(self.game_loop, "game_loop")

    def setup_environment(self):
        """Fények és háttérszín beállítása."""
        self.setBackgroundColor(0.5, 0.7, 0.9)

        alight = AmbientLight('alight')
        alight.setColor((0.4, 0.4, 0.4, 1))
        self.render.setLight(self.render.attachNewNode(alight))

        dlight = DirectionalLight('dlight')
        dlight.setColor((0.8, 0.8, 0.7, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(-45, -45, 0)
        self.render.setLight(dlnp)

    def setup_terrain(self):
        """A sziget legenerálása és elhelyezése."""
        print("Sziget generálása...")
        
        # Magasságtérkép generálása
        height_map = generate_island(size=129, height_scale=1.0, seed=42)
        
        # Radiális (kör alakú) sziget használata
        self.terrain = make_radial_island_nodepath(
            self, 
            height_map, 
            pos=(0, 0, -20), # Kicsit lejjebb, hogy legyen hely esni
            radius=150, 
            height_scale=30.0
        )
        
        self.terrain.reparentTo(self.render)
        self.terrain.setColor(0.2, 0.6, 0.3, 1) 
        self.terrain.setTwoSided(True)

    def setup_controls(self):
        for key in self.keys:
            self.accept(key, self.set_key, [key, True])
            self.accept(key+"-up", self.set_key, [key, False])
        
        self.accept("control", self.cam_manager.unlock_cursor)
        self.accept("control-up", self.cam_manager.lock_cursor)
        self.accept("escape", self.userExit)

    def set_key(self, key, value):
        self.keys[key] = value

    def game_loop(self, task):
        """Ez fut minden képkockában."""
        dt = globalClock.getDt()
        
        # 1. Kamera frissítése
        self.cam_manager.update()
        
        # 2. Fizika frissítése (Ez intézi a gravitációt és az ütközést)
        self.physics.update_physics(dt)
        
        # 3. Játékos VÍZSZINTES mozgatása
        cam_heading = self.cam_manager.get_heading()
        self.player.update_movement(dt, self.keys, cam_heading)
        
        return task.cont

if __name__ == "__main__":
    game = Game()
    game.run()