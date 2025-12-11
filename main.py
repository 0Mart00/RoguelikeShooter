import sys
from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, Vec3, CollisionTraverser

# --- Modulok ---
try:
    from terrain.infinite_terrain import InfiniteTerrain
    from core.player import Player
    from core.camera_manager import CameraManager
    from core.physics import PhysicsManager
    from core.enemy_ai import EnemyAI
    # ÚJ: Importáljuk a lövedéket
    from core.projectile import Projectile

except ImportError as e:
    print(f"HIBA: {e}"); sys.exit()

class Game(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse()
        
        # Környezet és Terep
        self.setup_environment()
        self.setup_terrain()

        # Játékos és Kamera
        self.player = Player(self.render, start_pos=(0, 0, 50))
        self.cam_manager = CameraManager(self, self.player.node)
        
        # Fizika
        self.physics = PhysicsManager(self)
        self.physics.setup_collision(self.player, self.terrain.root)
        
        # --- ÚJ: Lövedék Rendszer Setup ---
        # Külön Traverser a golyóknak, hogy gyors legyen
        self.bulletTrav = CollisionTraverser() 
        self.bullets = [] # Itt tároljuk az aktív golyókat

        # --- Ellenségek Létrehozása ---
        self.enemies = []
        # Több ellenséget rakunk le különböző helyekre
        spawn_points = [
            [Vec3(30, 30, 0), Vec3(30, -30, 0)],
            [Vec3(-30, 30, 0), Vec3(-30, -30, 0)],
            [Vec3(50, 0, 0), Vec3(60, 10, 0)]
        ]
        
        for patrol_route in spawn_points:
            enemy = EnemyAI(self, self.player, patrol_route)
            self.enemies.append(enemy)
        
        # Inputok
        self.keys = {"w": False, "s": False, "a": False, "d": False, "space": False}
        self.setup_controls()

        # UI
        from direct.gui.OnscreenText import OnscreenText
        self.info = OnscreenText(text="BAL KLIKK: Lövés | WASD: Mozgás",
                                 pos=(-0.9, 0.9), scale=0.05, align=0, fg=(1,1,1,1))

        self.taskMgr.add(self.game_loop, "game_loop")

    def setup_environment(self):
        self.setBackgroundColor(0.5, 0.7, 0.9)
        alight = AmbientLight('alight'); alight.setColor((0.4, 0.4, 0.4, 1))
        self.render.setLight(self.render.attachNewNode(alight))
        dlight = DirectionalLight('dlight'); dlight.setColor((0.8, 0.8, 0.7, 1))
        dlnp = self.render.attachNewNode(dlight); dlnp.setHpr(-45, -45, 0)
        self.render.setLight(dlnp)

    def setup_terrain(self):
        self.terrain = InfiniteTerrain(self.render, seed=42)

    def setup_controls(self):
        for key in self.keys:
            self.accept(key, self.set_key, [key, True])
            self.accept(key+"-up", self.set_key, [key, False])
        
        self.accept("control", self.cam_manager.unlock_cursor)
        self.accept("control-up", self.cam_manager.lock_cursor)
        
        # ÚJ: Lövés gomb
        self.accept("mouse1", self.shoot)
        
        self.accept("escape", self.userExit)

    def set_key(self, key, value):
        self.keys[key] = value

    def shoot(self):
        """Lövés esemény."""
        # A kamerából indul a golyó, a kamera irányába
        # A cam_manager.pivot helyett a valódi kamerát (self.camera) használjuk a pontos célzáshoz
        start_pos = self.camera.getPos(self.render)
        direction_quat = self.camera.getQuat(self.render)
        
        # Létrehozzuk a golyót
        bullet = Projectile(self, start_pos, direction_quat)
        self.bullets.append(bullet)

    def game_loop(self, task):
        dt = globalClock.getDt()
        
        self.terrain.update(self.player.node.getPos())
        self.cam_manager.update()
        self.physics.update_physics(dt)
        
        # ÚJ: Golyók frissítése
        # A 'traverse' ellenőrzi az ütközéseket az összes golyóra
        self.bulletTrav.traverse(self.render)
        
        # Frissítjük a golyók mozgását és töröljük a halottakat
        for bullet in self.bullets[:]: # Másolaton iterálunk, hogy törölhessünk
            bullet.update(dt)
            if not bullet.alive:
                self.bullets.remove(bullet)

        # Ellenségek listájának tisztítása (opcionális, ha törölni akarjuk a referenciát)
        self.enemies = [e for e in self.enemies if e.is_alive]

        cam_heading = self.cam_manager.get_heading()
        self.player.update_movement(dt, self.keys, cam_heading)
        
        return task.cont

if __name__ == "__main__":
    game = Game()
    game.run()