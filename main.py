import sys
from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, Vec3

# --- Modulok importálása ---
try:
    from terrain.generator import generate_island
    from terrain.terrain import make_island_nodepath, make_radial_island_nodepath
    
    from core.player import Player
    from core.camera_manager import CameraManager
    from core.physics import PhysicsManager
    
    # ÚJ: Importáljuk az Enemy AI-t
    from core.enemy_ai import EnemyAI

except ImportError as e:
    print("HIBA: Hiányzó fájlok vagy modulok!")
    print(f"Részletek: {e}")
    sys.exit()

class Game(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse()
        
        # 1. Környezet
        self.setup_environment()
        
        # 2. Terrain
        self.setup_terrain()

        # 3. Játékos
        self.player = Player(self.render, start_pos=(0, 0, 50))
        
        # 4. Kamera
        self.cam_manager = CameraManager(self, self.player.node)
        
        # 5. Fizika
        self.physics = PhysicsManager(self)
        self.physics.setup_collision(self.player, self.terrain)
        
        # 6. --- ÚJ: Enemy AI létrehozása ---
        # Járőr pontok a sziget körül (kb. 50 egységre a középponttól)
        patrol_points = [
            Vec3(40, 40, 0), Vec3(40, -40, 0), 
            Vec3(-40, -40, 0), Vec3(-40, 40, 0)
        ]
        self.enemy = EnemyAI(self, self.player, patrol_points)
        
        # 7. Inputok (Space hozzáadva)
        self.keys = {"w": False, "s": False, "a": False, "d": False, "space": False}
        self.setup_controls()

        # Info szöveg
        from direct.gui.OnscreenText import OnscreenText
        self.info = OnscreenText(text="WASD: Mozgás | SPACE: Zajkeltés (Vigyázz!)",
                                 pos=(-0.9, 0.9), scale=0.05, align=0, fg=(1,1,1,1))

        self.taskMgr.add(self.game_loop, "game_loop")

    def setup_environment(self):
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
        print("Sziget generálása...")
        height_map = generate_island(size=129, height_scale=1.0, seed=42)
        
        self.terrain = make_radial_island_nodepath(
            self, 
            height_map, 
            pos=(0, 0, -20), 
            radius=150, 
            height_scale=30.0
        )
        self.terrain.reparentTo(self.render)
        self.terrain.setColor(0.2, 0.6, 0.3, 1) 
        self.terrain.setTwoSided(True)

    def setup_controls(self):
        # Space hozzáadása a listához
        for key in self.keys:
            self.accept(key, self.set_key, [key, True])
            self.accept(key+"-up", self.set_key, [key, False])
        
        self.accept("control", self.cam_manager.unlock_cursor)
        self.accept("control-up", self.cam_manager.lock_cursor)
        self.accept("escape", self.userExit)

    def set_key(self, key, value):
        self.keys[key] = value

    def game_loop(self, task):
        dt = globalClock.getDt()
        
        self.cam_manager.update()
        self.physics.update_physics(dt)
        
        cam_heading = self.cam_manager.get_heading()
        self.player.update_movement(dt, self.keys, cam_heading)
        
        return task.cont

if __name__ == "__main__":
    game = Game()
    game.run()