from panda3d.core import Vec3, NodePath, GeomNode, GeomVertexFormat, GeomVertexData, GeomVertexWriter, GeomTriangles, Geom
from math import sin, cos, radians

class Player:
    def __init__(self, render_node, start_pos=(0, 0, 10)):
        self.speed = 10.0
        # Játékos vizuális megjelenítése (Kocka)
        self.node = self._make_box(2.0)
        self.node.reparentTo(render_node)
        self.node.setPos(start_pos)
        self.node.setColor(1, 0, 0, 1) # Piros szín

    def update_movement(self, dt, keys, camera_heading):
        """
        Frissíti a játékos pozícióját a gombok és a kamera iránya alapján.
        """
        direction = Vec3(0, 0, 0)
        
        # Input ellenőrzés
        if keys["w"]: direction.y += 1
        if keys["s"]: direction.y -= 1
        if keys["a"]: direction.x -= 1
        if keys["d"]: direction.x += 1

        if direction.length() > 0:
            direction.normalize()
            
            # Az irányt elforgatjuk a kamera nézési irányába
            h_rad = radians(camera_heading)
            rotated_dir = Vec3(
                direction.x * cos(h_rad) - direction.y * sin(h_rad),
                direction.x * sin(h_rad) + direction.y * cos(h_rad),
                0
            )
            
            # Pozíció frissítése
            current_pos = self.node.getPos()
            new_pos = current_pos + (rotated_dir * self.speed * dt)
            self.node.setPos(new_pos)

    def get_pos(self):
        return self.node.getPos()

    def _make_box(self, size):
        """Belső segédfüggvény a kocka geometria létrehozásához."""
        fmt = GeomVertexFormat.getV3n3()
        vdata = GeomVertexData("player_cube", fmt, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")

        hs = size / 2
        points = [
            (-hs,-hs,-hs), (hs,-hs,-hs), (hs,hs,-hs), (-hs,hs,-hs),
            (-hs,-hs,hs), (hs,-hs,hs), (hs,hs,hs), (-hs,hs,hs)
        ]
        
        for p in points:
            vertex.addData3(*p)
            normal.addData3(0, 0, 1)

        tris = GeomTriangles(Geom.UHStatic)
        faces = [
            (0,1,2,3), (4,5,6,7), (0,1,5,4),
            (2,3,7,6), (0,3,7,4), (1,2,6,5)
        ]
        for f in faces:
            tris.addVertices(f[0], f[1], f[2])
            tris.addVertices(f[0], f[2], f[3])

        geom = Geom(vdata)
        geom.addPrimitive(tris)
        node = GeomNode("player_cube")
        node.addGeom(geom)
        return NodePath(node)