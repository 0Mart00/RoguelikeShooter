from panda3d.core import (
    CollisionTraverser, CollisionHandlerQueue, 
    CollisionNode, CollisionRay, 
    BitMask32, NodePath, Vec3
)

class PhysicsManager:
    def __init__(self, base_app):
        self.base = base_app
        
        # Ütközés kezelők inicializálása
        # A Traverser végzi a vizsgálatot
        self.cTrav = CollisionTraverser()
        # A Queue tárolja a találatokat
        self.cQueue = CollisionHandlerQueue()
        
        # Fizikai konstansok
        self.gravity = 30.0    # Gravitációs erő
        self.terminal_velocity = 50.0 # Maximális esési sebesség

        # Ütközési maszk (hogy csak a talajjal ütközzünk)
        self.ground_mask = BitMask32.bit(1)

    def setup_collision(self, player_obj, terrain_node):
        """
        Beállítja a sugarat a játékoson és a maszkot a terepen.
        """
        self.player_obj = player_obj
        
        # 1. Sugár (Ray) létrehozása a játékosnál
        # A sugár 1 egységgel a talp felett indul (0,0,1) és lefelé mutat (0,0,-1)
        ray = CollisionRay()
        ray.setOrigin(0, 0, 1) 
        ray.setDirection(0, 0, -1)
        
        # Ütközési node létrehozása a sugárnak
        c_node = CollisionNode('player_ray')
        c_node.addSolid(ray)
        
        # Beállítjuk, hogy mit "lásson" a sugár (From mask)
        c_node.setFromCollideMask(self.ground_mask)
        # A sugárral magával nem akarunk ütközni (Into mask kikapcsolása)
        c_node.setIntoCollideMask(BitMask32.allOff())
        
        # Csatoljuk a játékoshoz
        self.c_np = self.player_obj.node.attachNewNode(c_node)
        
        # Hozzáadjuk a traverserhez
        self.cTrav.addCollider(self.c_np, self.cQueue)
        
        # 2. Terep beállítása
        # Fontos: A generált terrainnek be kell állítani az Into maszkját
        terrain_node.setCollideMask(self.ground_mask)
        
        # Debug: Ha látni akarod a sugarat, vedd ki a kommentet:
        # self.cTrav.showCollisions(self.base.render)

    def update_physics(self, dt):
        """
        Ezt kell hívni minden frame-ben. Kezeli a gravitációt és a talajfogást.
        """
        if not self.player_obj:
            return

        # 1. Gravitáció alkalmazása a sebességre
        self.player_obj.vertical_velocity -= self.gravity * dt
        
        # Maximális esési sebesség korlátozása
        if self.player_obj.vertical_velocity < -self.terminal_velocity:
            self.player_obj.vertical_velocity = -self.terminal_velocity

        # 2. Játékos mozgatása a Z tengelyen (becsült új pozíció)
        current_pos = self.player_obj.node.getPos()
        new_z = current_pos.z + self.player_obj.vertical_velocity * dt
        
        # 3. Ütközésvizsgálat (Lefuttatjuk a traversert)
        self.cTrav.traverse(self.base.render)
        
        # Megnézzük, találtunk-e talajt
        if self.cQueue.getNumEntries() > 0:
            # Rendezzük a találatokat (a legközelebbi érdekel)
            self.cQueue.sortEntries()
            entry = self.cQueue.getEntry(0)
            
            # Hol van a talaj felszíne?
            ground_point = entry.getSurfacePoint(self.base.render)
            ground_z = ground_point.z
            
            # LOGIKA: Ha a tervezett új pozíció a talaj ALÁ kerülne,
            # akkor megállítjuk a zuhanást és a talajra tesszük.
            # Egy kis tűréshatárt (offset) adunk, hogy ne rezegjen.
            if new_z <= ground_z:
                new_z = ground_z
                self.player_obj.vertical_velocity = 0 # Megállunk
                self.player_obj.is_grounded = True
            else:
                self.player_obj.is_grounded = False
        else:
            self.player_obj.is_grounded = False
            
        # 4. Pozíció frissítése
        self.player_obj.node.setZ(new_z)