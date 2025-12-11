import math
from panda3d.core import (
    Vec3, NodePath, BitMask32, CollisionTraverser, CollisionHandlerQueue,
    CollisionRay, CollisionSegment, CollisionNode, GeomNode
)
from direct.task import Task

# Maszkok
MASK_TERRAIN = BitMask32.bit(1)
MASK_PLAYER = BitMask32.bit(2)

class EnemyAI:
    STATE_IDLE = "Idle"
    STATE_PATROL = "Patrol"
    STATE_CHASE = "Chase"
    STATE_ATTACK = "Attack"
    STATE_SEARCH = "Search"

    def __init__(self, base_app, player_obj, patrol_points):
        self.base = base_app
        self.render = base_app.render
        self.player = player_obj
        self.patrol_points = patrol_points
        
        # --- Modell létrehozása (Saját kocka, hogy ne kelljen külső fájl) ---
        # Ha van 'box' modelled, használd a loader.loadModel("box")-ot
        self.actor = self.base.loader.loadModel("models/box") 
        self.actor.setScale(1.5, 1.5, 3.0) # Magasabb
        self.actor.setColor(1, 0.2, 0.2, 1) # Piros
        self.actor.reparentTo(self.render)
        self.actor.setPos(patrol_points[0]) # Kezdőpont

        # --- AI Paraméterek ---
        self.move_speed = 6.0
        self.run_speed = 11.0
        self.turn_speed = 200.0 # Fok/mp
        self.sight_range = 40.0
        self.fov_angle = 110.0
        self.hearing_range = 25.0
        self.attack_range = 4.0
        
        self.state = self.STATE_PATROL
        self.current_patrol_index = 0
        self.last_known_pos = None
        self.search_timer = 0
        
        # --- Érzékelés és Fizika (Raycast) ---
        self.cTrav = CollisionTraverser()
        self.cQueue = CollisionHandlerQueue()
        
        # 1. Látás sugár (Szem)
        self.sight_ray = CollisionSegment()
        self.sight_node = CollisionNode('ai_sight')
        self.sight_node.addSolid(self.sight_ray)
        self.sight_node.setFromCollideMask(MASK_TERRAIN | MASK_PLAYER)
        self.sight_node.setIntoCollideMask(BitMask32.allOff())
        self.sight_np = self.actor.attachNewNode(self.sight_node)
        self.cTrav.addCollider(self.sight_np, self.cQueue)

        # 2. Talaj sugár (Láb - Hogy ne essen le)
        self.foot_ray = CollisionRay(0, 0, 2, 0, 0, -1)
        self.foot_node = CollisionNode('ai_foot')
        self.foot_node.addSolid(self.foot_ray)
        self.foot_node.setFromCollideMask(MASK_TERRAIN)
        self.foot_node.setIntoCollideMask(BitMask32.allOff())
        self.foot_np = self.actor.attachNewNode(self.foot_node)
        self.cTrav.addCollider(self.foot_np, self.cQueue)

        # Task indítása
        self.base.taskMgr.add(self.update, "EnemyAIUpdate")
        print("Enemy AI elindult!")

    def update(self, task):
        dt = globalClock.getDt()
        
        # Távolság a játékostól
        dist_to_player = (self.actor.getPos() - self.player.get_pos()).length()
        
        # Talajhoz igazítás (Gravitáció-szerűség)
        self.snap_to_ground()

        # Érzékelés
        can_see = self.check_vision(dist_to_player)
        can_hear = self.check_hearing(dist_to_player)

        # Állapotgép (State Machine)
        if self.state == self.STATE_PATROL:
            if can_see or can_hear:
                self.found_player()
                
        elif self.state == self.STATE_CHASE:
            if not can_see and dist_to_player > 5.0:
                # Elvesztette a játékost
                self.state = self.STATE_SEARCH
                self.search_timer = 5.0 # 5 mp keresés
                self.last_known_pos = self.player.get_pos()
            elif dist_to_player <= self.attack_range:
                self.state = self.STATE_ATTACK
                
        elif self.state == self.STATE_ATTACK:
            if dist_to_player > self.attack_range:
                self.state = self.STATE_CHASE
                
        elif self.state == self.STATE_SEARCH:
            if can_see:
                self.found_player()
            elif self.search_timer <= 0:
                self.state = self.STATE_PATROL
            else:
                self.search_timer -= dt

        # Viselkedés végrehajtása
        if self.state == self.STATE_PATROL:
            self.behavior_patrol(dt)
        elif self.state == self.STATE_CHASE:
            self.behavior_chase(dt)
        elif self.state == self.STATE_ATTACK:
            self.behavior_attack(dt)
        elif self.state == self.STATE_SEARCH:
            self.behavior_search(dt)

        self.update_color()
        return Task.cont

    def snap_to_ground(self):
        """Sugárral megnézi, hol a talaj, és ráteszi az AI-t."""
        self.cTrav.traverse(self.render)
        # Megnézzük a foot_node találatait
        # (Mivel a queue közös a látással, szűrni kellene, de most egyszerűsítünk:
        # feltételezzük, hogy a látás sugár vízszintes, a láb függőleges)
        
        ground_z = -100 # Default mélység
        
        if self.cQueue.getNumEntries() > 0:
            self.cQueue.sortEntries()
            for i in range(self.cQueue.getNumEntries()):
                entry = self.cQueue.getEntry(i)
                # Csak a láb sugarát nézzük
                if entry.getFromNode() == self.foot_node:
                    ground_z = entry.getSurfacePoint(self.render).z
                    break
        
        # Finom igazítás (lerp), hogy ne ugráljon
        current_z = self.actor.getZ()
        if ground_z > -90:
            # +1.5 az offset (mivel a modell origója a közepén van)
            target_z = ground_z + 1.5
            new_z = current_z + (target_z - current_z) * 0.1
            self.actor.setZ(new_z)

    def check_vision(self, dist):
        if dist > self.sight_range: return False
        
        # Szög ellenőrzés (FOV)
        vec_to_player = self.player.get_pos() - self.actor.getPos()
        vec_to_player.normalize()
        forward = self.actor.getQuat().getForward()
        
        if forward.dot(vec_to_player) < math.cos(math.radians(self.fov_angle / 2.0)):
            return False 

        # Raycast ellenőrzés (Lát-e a falakon át?)
        start_pos = self.actor.getPos() + Vec3(0, 0, 1.0) # Szemmagasság
        end_pos = self.player.get_pos() + Vec3(0, 0, 0.5)
        
        self.sight_ray.setPointA(start_pos)
        self.sight_ray.setPointB(end_pos)
        
        self.cTrav.traverse(self.render)
        
        if self.cQueue.getNumEntries() > 0:
            self.cQueue.sortEntries()
            entry = self.cQueue.getEntry(0)
            # Ha az első dolog amit eltalál az a Player, akkor látja
            if entry.getIntoNode().getName() == "player_hitbox":
                self.last_known_pos = self.player.get_pos()
                return True
                
        return False

    def check_hearing(self, dist):
        if self.player.is_making_noise and dist <= self.hearing_range:
            self.last_known_pos = self.player.get_pos()
            return True
        return False

    def found_player(self):
        self.state = self.STATE_CHASE

    def rotate_towards(self, target_pos, dt):
        """Fordulás a cél felé."""
        target_pos.setZ(self.actor.getZ()) # Csak vízszintesen forduljon
        self.actor.headsUp(target_pos)

    def behavior_patrol(self, dt):
        target = self.patrol_points[self.current_patrol_index]
        dist = (target - self.actor.getPos()).lengthSquared()
        
        self.rotate_towards(target, dt)
        self.actor.setY(self.actor, self.move_speed * dt)
        
        if dist < 4.0: # Ha közel ért a ponthoz
            self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)

    def behavior_chase(self, dt):
        self.rotate_towards(self.player.get_pos(), dt)
        self.actor.setY(self.actor, self.run_speed * dt)

    def behavior_attack(self, dt):
        self.actor.lookAt(self.player.node)
        # Itt lehetne sebzést okozni
        
    def behavior_search(self, dt):
        if self.last_known_pos:
            self.rotate_towards(self.last_known_pos, dt)
            self.actor.setY(self.actor, self.run_speed * dt)

    def update_color(self):
        if self.state == self.STATE_PATROL: self.actor.setColor(0, 1, 0, 1) # Zöld
        elif self.state == self.STATE_CHASE: self.actor.setColor(1, 0.5, 0, 1) # Narancs
        elif self.state == self.STATE_ATTACK: self.actor.setColor(1, 0, 0, 1) # Piros
        elif self.state == self.STATE_SEARCH: self.actor.setColor(1, 1, 0, 1) # Sárga