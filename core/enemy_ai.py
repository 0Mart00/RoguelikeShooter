import math
import random
from panda3d.core import (
    Vec3, NodePath, BitMask32, CollisionTraverser, CollisionHandlerQueue,
    CollisionRay, CollisionSegment, CollisionNode, CollisionSphere
)
from direct.task import Task

MASK_TERRAIN = BitMask32.bit(1)
MASK_PLAYER = BitMask32.bit(2)
MASK_ENEMY = BitMask32.bit(3) # ÚJ: Ellenség maszk

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
        self.is_alive = True
        
        # Modell betöltése
        try:
            self.actor = self.base.loader.loadModel("models/box") 
        except:
            self.actor = self.base.loader.loadModel("box")
            
        self.actor.setScale(1.5, 1.5, 3.0)
        self.actor.setColor(1, 0.2, 0.2, 1) # Piros
        self.actor.reparentTo(self.render)
        self.actor.setPos(patrol_points[0])

        # --- ÚJ: Hitbox létrehozása (hogy a golyó eltalálhassa) ---
        hitbox_node = CollisionNode('enemy_hitbox')
        hitbox_node.addSolid(CollisionSphere(0, 0, 0, 1.0)) # A test közepe
        hitbox_node.setIntoCollideMask(MASK_ENEMY) # Ebbe ütközik a golyó
        hitbox_node.setFromCollideMask(BitMask32.allOff())
        self.hitbox_np = self.actor.attachNewNode(hitbox_node)
        # Rárakjuk a Python Tag-et, hogy a golyó tudja, kibe lőtt bele
        self.hitbox_np.setPythonTag("owner", self)

        # AI Paraméterek
        self.move_speed = 6.0
        self.run_speed = 11.0
        self.sight_range = 40.0
        self.fov_angle = 110.0
        self.hearing_range = 25.0
        self.attack_range = 4.0
        
        self.state = self.STATE_PATROL
        self.current_patrol_index = 0
        self.last_known_pos = None
        self.search_timer = 0
        
        # Érzékelés (Saját Traverser)
        self.cTrav = CollisionTraverser()
        self.cQueue = CollisionHandlerQueue()
        
        # Látás és Láb sugarak (a korábbi kódból)
        self.sight_ray = CollisionSegment()
        self.sight_node = CollisionNode('ai_sight')
        self.sight_node.addSolid(self.sight_ray)
        self.sight_node.setFromCollideMask(MASK_TERRAIN | MASK_PLAYER)
        self.sight_node.setIntoCollideMask(BitMask32.allOff())
        self.sight_np = self.actor.attachNewNode(self.sight_node)
        self.cTrav.addCollider(self.sight_np, self.cQueue)

        # JAVÍTÁS: A láb sugár magasabbról (Z=30) indul, hogy ne kerüljön föld alá
        self.foot_ray = CollisionRay(0, 0, 30, 0, 0, -1)
        self.foot_node = CollisionNode('ai_foot')
        self.foot_node.addSolid(self.foot_ray)
        self.foot_node.setFromCollideMask(MASK_TERRAIN)
        self.foot_node.setIntoCollideMask(BitMask32.allOff())
        self.foot_np = self.actor.attachNewNode(self.foot_node)
        self.cTrav.addCollider(self.foot_np, self.cQueue)

        # Task indítása (Egyedi névvel, hogy törölhető legyen)
        self.task_name = f"EnemyAIUpdate_{id(self)}"
        self.base.taskMgr.add(self.update, self.task_name)

    def take_damage(self):
        """Ezt hívja meg a golyó, ha eltalál."""
        print("Ellenség meghalt!")
        self.die()

    def die(self):
        """Ellenség megsemmisítése."""
        if not self.is_alive: return
        self.is_alive = False
        
        # Task leállítása
        self.base.taskMgr.remove(self.task_name)
        
        # Node törlése
        self.actor.removeNode()

    def update(self, task):
        if not self.is_alive: return Task.done
        
        dt = globalClock.getDt()
        dist_to_player = (self.actor.getPos() - self.player.get_pos()).length()
        
        self.snap_to_ground()
        
        can_see = self.check_vision(dist_to_player)
        can_hear = self.check_hearing(dist_to_player)

        # Állapotgép
        if self.state == self.STATE_PATROL:
            if can_see or can_hear: self.state = self.STATE_CHASE
        elif self.state == self.STATE_CHASE:
            if not can_see and dist_to_player > 10.0:
                self.state = self.STATE_SEARCH; self.search_timer = 5.0; self.last_known_pos = self.player.get_pos()
            elif dist_to_player <= self.attack_range:
                self.state = self.STATE_ATTACK
        elif self.state == self.STATE_ATTACK:
            if dist_to_player > self.attack_range: self.state = self.STATE_CHASE
        elif self.state == self.STATE_SEARCH:
            if can_see: self.state = self.STATE_CHASE
            elif self.search_timer <= 0: self.state = self.STATE_PATROL
            else: self.search_timer -= dt

        # Viselkedés
        if self.state == self.STATE_PATROL: self.behavior_patrol(dt)
        elif self.state == self.STATE_CHASE: self.behavior_chase(dt)
        elif self.state == self.STATE_ATTACK: self.behavior_attack(dt)
        elif self.state == self.STATE_SEARCH: self.behavior_search(dt)

        self.update_color()
        return Task.cont

    # --- Segédfüggvények (változatlanok vagy egyszerűsítve) ---
    def snap_to_ground(self):
        self.cTrav.traverse(self.render)
        ground_z = -100
        if self.cQueue.getNumEntries() > 0:
            self.cQueue.sortEntries()
            for i in range(self.cQueue.getNumEntries()):
                entry = self.cQueue.getEntry(i)
                if entry.getFromNode() == self.foot_node:
                    ground_z = entry.getSurfacePoint(self.render).z; break
        
        current_z = self.actor.getZ()
        if ground_z > -90: 
            target_z = ground_z + 1.5
            # JAVÍTÁS: Kicsit gyorsabb lerp (0.2) és snap, ha közel van, hogy ne remegjen
            diff = target_z - current_z
            if abs(diff) < 0.1:
                self.actor.setZ(target_z)
            else:
                self.actor.setZ(current_z + diff * 0.2)

    def check_vision(self, dist):
        if dist > self.sight_range: return False
        vec = self.player.get_pos() - self.actor.getPos(); vec.normalize()
        fwd = self.actor.getQuat().getForward()
        if fwd.dot(vec) < math.cos(math.radians(self.fov_angle/2)): return False
        
        start = self.actor.getPos() + Vec3(0,0,1)
        end = self.player.get_pos() + Vec3(0,0,0.5)
        self.sight_ray.setPointA(start); self.sight_ray.setPointB(end)
        self.cTrav.traverse(self.render)
        if self.cQueue.getNumEntries() > 0:
            self.cQueue.sortEntries()
            if self.cQueue.getEntry(0).getIntoNode().getName() == "player_hitbox":
                self.last_known_pos = self.player.get_pos(); return True
        return False

    def check_hearing(self, dist):
        if self.player.is_making_noise and dist <= self.hearing_range:
            self.last_known_pos = self.player.get_pos(); return True
        return False

    def rotate_towards(self, pos, dt):
        pos.setZ(self.actor.getZ()); self.actor.headsUp(pos)
    
    def behavior_patrol(self, dt):
        target = self.patrol_points[self.current_patrol_index]
        self.rotate_towards(target, dt); self.actor.setY(self.actor, self.move_speed*dt)
        if (target - self.actor.getPos()).lengthSquared() < 4.0: self.current_patrol_index = (self.current_patrol_index+1)%len(self.patrol_points)

    def behavior_chase(self, dt):
        self.rotate_towards(self.player.get_pos(), dt); self.actor.setY(self.actor, self.run_speed*dt)
    def behavior_attack(self, dt): self.actor.lookAt(self.player.node)
    def behavior_search(self, dt):
        if self.last_known_pos: self.rotate_towards(self.last_known_pos, dt); self.actor.setY(self.actor, self.run_speed*dt)
    def update_color(self):
        if self.state==self.STATE_PATROL: self.actor.setColor(0,1,0,1)
        elif self.state==self.STATE_CHASE: self.actor.setColor(1,0.5,0,1)
        elif self.state==self.STATE_ATTACK: self.actor.setColor(1,0,0,1)
        elif self.state==self.STATE_SEARCH: self.actor.setColor(1,1,0,1)