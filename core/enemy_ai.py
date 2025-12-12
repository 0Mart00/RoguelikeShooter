import math
from panda3d.core import (
    Vec3, NodePath, BitMask32, CollisionTraverser, CollisionHandlerQueue,
    CollisionRay, CollisionSegment, CollisionNode, GeomNode, CollisionSphere
)
from direct.task import Task
from direct.actor.Actor import Actor

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
        
        # --- MODELL BETÖLTÉSE ---
        # Ha statikus a modell (nincs animáció), az Actor akkor is betölti a geometriát.
        # Üres szótárat adunk át, vagy csak a fájlt.
        self.actor = Actor("assets/models/monkey.egg", {})

        self.actor.setScale(0.5, 0.5, 0.5) 
        self.actor.reparentTo(self.render)
        self.actor.setPos(patrol_points[0])
        
        # Animáció állapot követése
        self.current_anim = None

        # --- AI Paraméterek ---
        self.move_speed = 6.0
        self.run_speed = 11.0
        self.turn_speed = 200.0 
        self.sight_range = 40.0
        self.fov_angle = 110.0
        self.hearing_range = 25.0
        self.attack_range = 4.0
        
        self.state = self.STATE_PATROL
        self.current_patrol_index = 0
        self.last_known_pos = None
        self.search_timer = 0
        
        # --- Élet Állapot ---
        self.is_alive = True
        self.health = 3
        
        # --- Érzékelés és Fizika (Raycast) ---
        self.cTrav = CollisionTraverser()
        self.cQueue = CollisionHandlerQueue()
        
        # 1. Látás sugár
        self.sight_ray = CollisionSegment()
        self.sight_node = CollisionNode('ai_sight')
        self.sight_node.addSolid(self.sight_ray)
        self.sight_node.setFromCollideMask(MASK_TERRAIN | MASK_PLAYER)
        self.sight_node.setIntoCollideMask(BitMask32.allOff())
        self.sight_np = self.actor.attachNewNode(self.sight_node)
        self.cTrav.addCollider(self.sight_np, self.cQueue)

        # 2. Talaj sugár
        self.foot_ray = CollisionRay(0, 0, 2, 0, 0, -1)
        self.foot_node = CollisionNode('ai_foot')
        self.foot_node.addSolid(self.foot_ray)
        self.foot_node.setFromCollideMask(MASK_TERRAIN)
        self.foot_node.setIntoCollideMask(BitMask32.allOff())
        self.foot_np = self.actor.attachNewNode(self.foot_node)
        self.cTrav.addCollider(self.foot_np, self.cQueue)
        
        # --- Hitbox ---
        c_sphere = CollisionNode('enemy_hitbox')
        c_sphere.addSolid(CollisionSphere(0, 0, 2, 2.0))
        c_sphere.setIntoCollideMask(BitMask32.bit(3))
        c_sphere.setFromCollideMask(BitMask32.allOff())
        self.hitbox_np = self.actor.attachNewNode(c_sphere)
        self.hitbox_np.setPythonTag("enemy", self)

        self.base.taskMgr.add(self.update, "EnemyAIUpdate")
        print("Enemy AI (Monkey) elindult!")

    def set_anim(self, anim_name, loop=True):
        """Animáció váltása biztonságosan."""
        if self.current_anim != anim_name:
            try:
                # JAVÍTÁS: Itt történik a hiba, ha a modell statikus.
                # A getAnimNames() IndexErrort dob, ha nincs karakter struktúra.
                # Elkapjuk a hibákat (IndexError, AttributeError) és csendben folytatjuk.
                if anim_name in self.actor.getAnimNames():
                    if loop:
                        self.actor.loop(anim_name)
                    else:
                        self.actor.play(anim_name)
                    self.current_anim = anim_name
            except (IndexError, AttributeError, ValueError):
                # Statikus modell detektálva, vagy nincs animáció -> Nem csinálunk semmit
                pass
            except Exception as e:
                # Bármi más hiba esetén sem omlunk össze, de nem spamoljuk a konzolt
                pass
    
    def take_damage(self, amount=1):
        if not self.is_alive: return
        self.health -= amount
        print(f"Enemy hit! Health: {self.health}")
        if self.health <= 0:
            self.die()

    def die(self):
        if not self.is_alive: return
        self.is_alive = False
        print("Enemy died!")
        self.actor.cleanup()
        self.actor.removeNode()

    def update(self, task):
        if not self.is_alive:
            return Task.done
            
        dt = globalClock.getDt()
        
        dist_to_player = (self.actor.getPos() - self.player.get_pos()).length()
        
        self.snap_to_ground()

        can_see = self.check_vision(dist_to_player)
        can_hear = self.check_hearing(dist_to_player)

        # Állapotgép (Animáció kérésekkel, amik most már biztonságosak)
        if self.state == self.STATE_PATROL:
            self.set_anim("walk") 
            if can_see or can_hear:
                self.found_player()
                
        elif self.state == self.STATE_CHASE:
            self.set_anim("run")
            if not can_see and dist_to_player > 5.0:
                self.state = self.STATE_SEARCH
                self.search_timer = 5.0
                self.last_known_pos = self.player.get_pos()
            elif dist_to_player <= self.attack_range:
                self.state = self.STATE_ATTACK
                
        elif self.state == self.STATE_ATTACK:
            self.set_anim("attack")
            if dist_to_player > self.attack_range:
                self.state = self.STATE_CHASE
                
        elif self.state == self.STATE_SEARCH:
            self.set_anim("walk")
            if can_see:
                self.found_player()
            elif self.search_timer <= 0:
                self.state = self.STATE_PATROL
            else:
                self.search_timer -= dt

        # Viselkedés
        if self.state == self.STATE_PATROL:
            self.behavior_patrol(dt)
        elif self.state == self.STATE_CHASE:
            self.behavior_chase(dt)
        elif self.state == self.STATE_ATTACK:
            self.behavior_attack(dt)
        elif self.state == self.STATE_SEARCH:
            self.behavior_search(dt)

        return Task.cont

    def snap_to_ground(self):
        self.cTrav.traverse(self.render)
        ground_z = -100
        
        if self.cQueue.getNumEntries() > 0:
            self.cQueue.sortEntries()
            for i in range(self.cQueue.getNumEntries()):
                entry = self.cQueue.getEntry(i)
                if entry.getFromNode() == self.foot_node:
                    ground_z = entry.getSurfacePoint(self.render).z
                    break
        
        current_z = self.actor.getZ()
        if ground_z > -90:
            ground_offset = 0.5 
            target_z = ground_z + ground_offset
            new_z = current_z + (target_z - current_z) * 0.2
            self.actor.setZ(new_z)

    def check_vision(self, dist):
        if dist > self.sight_range: return False
        
        vec_to_player = self.player.get_pos() - self.actor.getPos()
        vec_to_player.normalize()
        forward = self.actor.getQuat().getForward()
        
        if forward.dot(vec_to_player) < math.cos(math.radians(self.fov_angle / 2.0)):
            return False 

        start_pos = self.actor.getPos() + Vec3(0, 0, 1.0) 
        end_pos = self.player.get_pos() + Vec3(0, 0, 0.5)
        
        self.sight_ray.setPointA(start_pos)
        self.sight_ray.setPointB(end_pos)
        
        self.cTrav.traverse(self.render)
        
        if self.cQueue.getNumEntries() > 0:
            self.cQueue.sortEntries()
            entry = self.cQueue.getEntry(0)
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
        target_pos.setZ(self.actor.getZ())
        self.actor.headsUp(target_pos)

    def behavior_patrol(self, dt):
        target = self.patrol_points[self.current_patrol_index]
        dist = (target - self.actor.getPos()).lengthSquared()
        
        self.rotate_towards(target, dt)
        self.actor.setY(self.actor, self.move_speed * dt)
        
        if dist < 4.0:
            self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)

    def behavior_chase(self, dt):
        self.rotate_towards(self.player.get_pos(), dt)
        self.actor.setY(self.actor, self.run_speed * dt)

    def behavior_attack(self, dt):
        self.actor.lookAt(self.player.node)

    def behavior_search(self, dt):
        if self.last_known_pos:
            self.rotate_towards(self.last_known_pos, dt)
            self.actor.setY(self.actor, self.run_speed * dt)