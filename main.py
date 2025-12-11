import sys
from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, Vec3

# --- Modulok importálása ---
try:
    # ÚJ: Az InfiniteTerrain importálása
    from terrain.infinite_terrain import InfiniteTerrain
    
    from core.player import Player
    from core.camera_manager import CameraManager
    from core.physics import PhysicsManager
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
        
        # 2. Végtelen Terep Létrehozása
        # (A setup_terrain metódus már az új osztályt használja)
        self.setup_terrain()

        # 3. Játékos
        # Magasabbról indítjuk, biztos, ami biztos
        self.player = Player(self.render, start_pos=(0, 0, 50))
        
        # 4. Kamera
        self.cam_manager = CameraManager(self, self.player.node)
        
        # 5. Fizika
        self.physics = PhysicsManager(self)
        # Itt átadjuk az infinite terrain root node-ját (self.terrain.root)
        # Fontos: Az infinite_terrain.py-ban beállítottuk a collision maskot,
        # így a PhysicsManager sugara érzékelni fogja a chunkokat.
        self.physics.setup_collision(self.player, self.terrain.root)
        
        # 6. Enemy AI
        # Figyelem: A járőrpontok most a végtelen terepen lesznek.
        # Az AI Raycastja is működni fog a terrain mask miatt.
        patrol_points = [
            Vec3(40, 40, 0), Vec3(40, -40, 0), 
            Vec3(-40, -40, 0), Vec3(-40, 40, 0)
        ]
        self.enemy = EnemyAI(self, self.player, patrol_points)
        
        # 7. Inputok
        self.keys = {"w": False, "s": False, "a": False, "d": False, "space": False}
        self.setup_controls()

        # Info szöveg
        from direct.gui.OnscreenText import OnscreenText
        self.info = OnscreenText(text="Végtelen Terep | WASD: Mozgás | SPACE: Zaj",
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
        print("Végtelen terep inicializálása...")
        # Létrehozzuk az új rendszert
        self.terrain = InfiniteTerrain(self.render, seed=42)

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
        dt = globalClock.getDt()
        
        # 1. Terep frissítése a játékos pozíciója alapján
        # Ez tölti be az új chunkokat, mielőtt a fizika futna
        self.terrain.update(self.player.node.getPos())
        
        # 2. Kamera
        self.cam_manager.update()
        
        # 3. Fizika
        self.physics.update_physics(dt)
        
        # 4. Játékos mozgás
        cam_heading = self.cam_manager.get_heading()
        self.player.update_movement(dt, self.keys, cam_heading)
        
        return task.cont

if __name__ == "__main__":
    game = Game()
    game.run()