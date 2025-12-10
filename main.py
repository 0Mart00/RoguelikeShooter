from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath, Vec3, WindowProperties, GeomNode, GeomVertexFormat, GeomVertexData, GeomVertexWriter, GeomTriangles, Geom
from math import sin, cos, radians, pi

class Game(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse()

        # Kamera paraméterek
        self.cam_distance = 10
        self.cam_height = 2
        self.cam_speed = 100
        self.prev_mouse_pos = None

        # Player kocka
        self.player = self.make_box(2.0)
        self.player.reparentTo(self.render)
        self.player.setPos(0,0,0)

        # Pivot a kamera számára
        self.cam_pivot = NodePath("cam_pivot")
        self.cam_pivot.reparentTo(self.render)
        self.camera.reparentTo(self.cam_pivot)
        self.camera.setPos(0, -self.cam_distance, self.cam_height)
        self.camera.lookAt(self.cam_pivot)

        # WASD input
        self.keys = {"w":False,"s":False,"a":False,"d":False}
        for key in self.keys:
            self.accept(key, self.set_key, [key, True])
            self.accept(key+"-up", self.set_key, [key, False])

        # Kurzor lock
        self.cursor_locked = True
        self.lock_cursor()
        self.accept("control", self.unlock_cursor)
        self.accept("control-up", self.lock_cursor)

        # Task-ok
        self.taskMgr.add(self.update_player, "update_player")
        self.taskMgr.add(self.update_camera, "update_camera")

    # -----------------------------
    # Kurzor lock/unlock
    # -----------------------------
    def lock_cursor(self):
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_confined)
        self.win.requestProperties(props)
        self.cursor_locked = True
        self.prev_mouse_pos = None

    def unlock_cursor(self):
        props = WindowProperties()
        props.setCursorHidden(False)
        props.setMouseMode(WindowProperties.M_absolute)
        self.win.requestProperties(props)
        self.cursor_locked = False

    # -----------------------------
    # Egérrel forgatható kamera
    # -----------------------------
    def update_camera(self, task):
        if self.cursor_locked and self.mouseWatcherNode.hasMouse():
            x = self.mouseWatcherNode.getMouseX()
            y = self.mouseWatcherNode.getMouseY()
            if self.prev_mouse_pos is not None:
                dx = x - self.prev_mouse_pos[0]
                dy = y - self.prev_mouse_pos[1]

                # Delta alapján frissítés
                new_h = self.cam_pivot.getH() - dx * self.cam_speed
                new_p = self.cam_pivot.getP() + dy * self.cam_speed

                # Pitch korlátozása
                new_p = max(-89, min(89, new_p))

                self.cam_pivot.setH(new_h)
                self.cam_pivot.setP(new_p)

            self.prev_mouse_pos = (x, y)

        # Pivot követi a játékost
        self.cam_pivot.setPos(self.player.getPos())
        return task.cont

    # -----------------------------
    # WASD játékos mozgatás
    # -----------------------------
    def set_key(self, key, value):
        self.keys[key] = value

    def update_player(self, task):
        dt = globalClock.getDt()
        speed = 5
        pos = self.player.getPos()
        direction = Vec3(0,0,0)
        if self.keys["w"]: direction.y += 1
        if self.keys["s"]: direction.y -= 1
        if self.keys["a"]: direction.x -= 1
        if self.keys["d"]: direction.x += 1

        if direction.length() > 0:
            direction.normalize()
            # Pivot H alapján forgatás a kamera irányába
            h = radians(self.cam_pivot.getH())
            rotated_dir = Vec3(
                direction.x * cos(h) - direction.y * sin(h),
                direction.x * sin(h) + direction.y * cos(h),
                0
            )
            pos += rotated_dir * speed * dt
            self.player.setPos(pos)

        return task.cont

    # -----------------------------
    # Kocka létrehozása
    # -----------------------------
    def make_box(self, size):
        fmt = GeomVertexFormat.getV3n3()
        vdata = GeomVertexData("cube", fmt, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")

        hs = size/2
        points = [
            (-hs,-hs,-hs), (hs,-hs,-hs), (hs,hs,-hs), (-hs,hs,-hs),
            (-hs,-hs,hs), (hs,-hs,hs), (hs,hs,hs), (-hs,hs,hs)
        ]
        for p in points:
            vertex.addData3(*p)
        for _ in points:
            normal.addData3(0,0,1)

        tris = GeomTriangles(Geom.UHStatic)
        faces = [
            (0,1,2,3), (4,5,6,7), (0,1,5,4),
            (2,3,7,6), (0,3,7,4), (1,2,6,5)
        ]
        for f in faces:
            tris.addVertices(f[0],f[1],f[2])
            tris.addVertices(f[0],f[2],f[3])

        geom = Geom(vdata)
        geom.addPrimitive(tris)
        node = GeomNode("cube")
        node.addGeom(geom)
        return NodePath(node)

game = Game()
game.run()
