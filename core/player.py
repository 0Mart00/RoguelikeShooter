from panda3d.core import Vec3, NodePath, GeomNode, GeomVertexFormat, GeomVertexData, GeomVertexWriter, GeomTriangles, Geom, BitMask32, CollisionNode, CollisionSphere
from math import sin, cos, radians

class Player:
    def __init__(self, render_node, start_pos=(0, 0, 50)):
        self.speed = 10.0
        self.vertical_velocity = 0.0
        self.is_grounded = False
        
        # --- ÚJ: Zaj indikátor az AI számára ---
        self.is_making_noise = False 

        # Játékos vizuális megjelenítése
        self.node = self._make_box(2.0)
        self.node.reparentTo(render_node)
        self.node.setPos(start_pos)
        self.node.setColor(1, 0, 0, 1)

        # --- ÚJ: Collision Node az AI látásához/találatához ---
        # A 2-es bitet használjuk a játékosra
        c_node = CollisionNode('player_hitbox')
        c_node.addSolid(CollisionSphere(0, 0, 0, 1.5))
        c_node.setIntoCollideMask(BitMask32.bit(2)) 
        c_node.setFromCollideMask(BitMask32.allOff())
        self.node.attachNewNode(c_node)

    def update_movement(self, dt, keys, camera_heading):
        # Zaj kezelése (Space gomb)
        # Feltételezzük, hogy a 'space' benne van a keys-ben (majd a main-ben berakjuk)
        if "space" in keys:
            self.is_making_noise = keys["space"]
        else:
            self.is_making_noise = False

        # --- Régi mozgás logika ---
        direction = Vec3(0, 0, 0)
        if keys["w"]: direction.y += 1
        if keys["s"]: direction.y -= 1
        if keys["a"]: direction.x -= 1
        if keys["d"]: direction.x += 1

        if direction.length() > 0:
            direction.normalize()
            h_rad = radians(camera_heading)
            rotated_dir = Vec3(
                direction.x * cos(h_rad) - direction.y * sin(h_rad),
                direction.x * sin(h_rad) + direction.y * cos(h_rad),
                0
            )
            current_pos = self.node.getPos()
            new_pos = current_pos + (rotated_dir * self.speed * dt)
            self.node.setX(new_pos.x)
            self.node.setY(new_pos.y)

    def get_pos(self):
        return self.node.getPos()

    def _make_box(self, size):
        # ... (Ez a rész változatlan, a kocka generáló kód) ...
        fmt = GeomVertexFormat.getV3n3()
        vdata = GeomVertexData("player_cube", fmt, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        hs = size / 2
        points = [(-hs,-hs,-hs), (hs,-hs,-hs), (hs,hs,-hs), (-hs,hs,-hs),
                  (-hs,-hs,hs), (hs,-hs,hs), (hs,hs,hs), (-hs,hs,hs)]
        for p in points:
            vertex.addData3(*p); normal.addData3(0, 0, 1)
        tris = GeomTriangles(Geom.UHStatic)
        faces = [(0,1,2,3), (4,5,6,7), (0,1,5,4), (2,3,7,6), (0,3,7,4), (1,2,6,5)]
        for f in faces:
            tris.addVertices(f[0], f[1], f[2]); tris.addVertices(f[0], f[2], f[3])
        geom = Geom(vdata); geom.addPrimitive(tris)
        node = GeomNode("player_cube"); node.addGeom(geom)
        return NodePath(node)