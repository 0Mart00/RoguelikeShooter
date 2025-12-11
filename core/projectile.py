from panda3d.core import (
    NodePath, Vec3, CollisionNode, CollisionSphere, 
    BitMask32, CollisionHandlerQueue
)

# Maszkok importálása vagy definíciója (hogy tudjuk mivel ütközünk)
MASK_TERRAIN = BitMask32.bit(1)
MASK_ENEMY = BitMask32.bit(3) # ÚJ: Az ellenség maszkja

class Projectile:
    def __init__(self, base_app, start_pos, direction_quat, speed=100.0):
        self.base = base_app
        self.speed = speed
        self.lifetime = 3.0 # Hány másodpercig él a golyó
        self.alive = True

        # 1. Modell létrehozása (kis sárga gömb)
        # Ha nincs 'sphere' modelled, a Panda3D beépítettjét is használhatod, 
        # vagy egy 'loader.loadModel("models/misc/sphere")'-t.
        # Itt most egy egyszerű modell betöltést feltételezünk:
        try:
            self.node = self.base.loader.loadModel("models/misc/sphere")
        except:
            # Fallback, ha nincs sphere modell
            self.node = self.base.loader.loadModel("box") 
            
        self.node.reparentTo(self.base.render)
        self.node.setScale(0.5) # Kicsi golyó
        self.node.setColor(1, 1, 0, 1) # Sárga
        self.node.setPos(start_pos)
        self.node.setQuat(direction_quat) # Arra néz, amerre a kamera

        # 2. Ütközésvizsgálat (Collision)
        self.cQueue = CollisionHandlerQueue()
        
        # Kis gömb ütköző a golyó köré
        c_node = CollisionNode('bullet_collider')
        c_node.addSolid(CollisionSphere(0, 0, 0, 1.0))
        
        # Kivel akarunk ütközni? (Ellenséggel és Tereppel)
        c_node.setFromCollideMask(MASK_ENEMY | MASK_TERRAIN)
        c_node.setIntoCollideMask(BitMask32.allOff()) # Más golyó ne találja el ezt
        
        self.c_np = self.node.attachNewNode(c_node)
        
        # Hozzáadjuk a golyót a játék fő CollisionTraverser-éhez
        # (Ezt majd a main.py-ban hozzuk létre 'self.bulletTrav' néven)
        self.base.bulletTrav.addCollider(self.c_np, self.cQueue)
        
        # Tag, hogy a golyó tudja magáról, ki ő (opcionális)
        self.node.setPythonTag("owner", self)

    def update(self, dt):
        if not self.alive: return
        
        # Mozgás előre (saját Y tengelye mentén)
        self.node.setY(self.node, self.speed * dt)
        
        # Élettartam csökkentése
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.destroy()
            return

        # Ütközések ellenőrzése
        if self.cQueue.getNumEntries() > 0:
            self.cQueue.sortEntries()
            entry = self.cQueue.getEntry(0)
            hit_node = entry.getIntoNode()
            hit_path = entry.getIntoNodePath()
            
            # Ha ellenséget találtunk
            if hit_node.getName() == "enemy_hitbox":
                # Lekérjük az ellenség objektumot a tag-ből
                enemy = hit_path.getPythonTag("owner")
                if enemy:
                    print("Találat!")
                    enemy.take_damage()
                self.destroy() # A golyó megsemmisül
                
            # Ha terepet találtunk (falat)
            elif hit_node.getName() == "chunk_node" or hit_path.hasNetTag("terrain"):
                 self.destroy()

    def destroy(self):
        if self.alive:
            self.alive = False
            self.base.bulletTrav.removeCollider(self.c_np)
            self.node.removeNode()