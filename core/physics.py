from panda3d.core import (
    CollisionTraverser, CollisionHandlerQueue, 
    CollisionNode, CollisionRay, 
    BitMask32, NodePath, Vec3
)

class PhysicsManager:
    def __init__(self, base_app):
        self.base = base_app
        
        # Ütközés kezelők inicializálása
        self.cTrav = CollisionTraverser()
        self.cQueue = CollisionHandlerQueue()
        
        # Fizikai konstansok
        self.gravity = 30.0
        self.terminal_velocity = 50.0
        self.ground_mask = BitMask32.bit(1)
        self.player_obj = None
        
        # ÚJ: Offset a játékos középpontja és talpa között.
        # Mivel a kocka 2.0 egység magas és az origója középen van,
        # 1.0-val feljebb kell tolni, hogy a talpa érje a földet.
        self.player_height_offset = 1.0

    def setup_collision(self, player_obj, terrain_node):
        """
        Beállítja a sugarat a játékoson és a maszkot a terepen.
        """
        self.player_obj = player_obj
        
        # A sugarat magasabbról (Z=50) indítjuk, hogy meredek lejtőn se kerüljön föld alá a kezdőpont
        ray = CollisionRay()
        ray.setOrigin(0, 0, 50) 
        ray.setDirection(0, 0, -1)
        
        c_node = CollisionNode('player_ray')
        c_node.addSolid(ray)
        
        c_node.setFromCollideMask(self.ground_mask)
        c_node.setIntoCollideMask(BitMask32.allOff())
        
        self.c_np = self.player_obj.node.attachNewNode(c_node)
        self.cTrav.addCollider(self.c_np, self.cQueue)

    def update_physics(self, dt):
        if not self.player_obj:
            return

        # 1. Gravitáció alkalmazása
        self.player_obj.vertical_velocity -= self.gravity * dt
        
        if self.player_obj.vertical_velocity < -self.terminal_velocity:
            self.player_obj.vertical_velocity = -self.terminal_velocity

        # 2. Becsült új pozíció
        current_pos = self.player_obj.node.getPos()
        new_z = current_pos.z + self.player_obj.vertical_velocity * dt
        
        # 3. Ütközésvizsgálat
        self.cTrav.traverse(self.base.render)
        
        if self.cQueue.getNumEntries() > 0:
            self.cQueue.sortEntries()
            entry = self.cQueue.getEntry(0)
            
            ground_point = entry.getSurfacePoint(self.base.render)
            ground_z = ground_point.z
            
            # JAVÍTOTT LOGIKA:
            # Nem a nyers ground_z-hez hasonlítunk, hanem hozzáadjuk az offsetet.
            # Így a "target_z" az a magasság, ahol a játékos KÖZEPÉNEK kell lennie ahhoz,
            # hogy a TALPA a földön legyen.
            target_z = ground_z + self.player_height_offset
            
            # Ha a tervezett új pozíció lejjebb van, mint a cél magasság...
            if new_z <= target_z:
                new_z = target_z # ...akkor felemeljük a helyes szintre
                self.player_obj.vertical_velocity = 0
                self.player_obj.is_grounded = True
            else:
                self.player_obj.is_grounded = False
        else:
            self.player_obj.is_grounded = False
            
        # 4. Pozíció frissítése
        self.player_obj.node.setZ(new_z)