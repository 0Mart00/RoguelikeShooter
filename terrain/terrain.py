# terrain/terrain.py
import numpy as np
from panda3d.core import Geom, GeomNode, GeomTriangles, GeomVertexFormat
from panda3d.core import GeomVertexWriter, GeomVertexData, NodePath, Vec3
from panda3d.core import GeomVertexReader
from panda3d.core import Shader

def compute_normals(vertices, size):
    """Egyszerű normál számítás cél: középpont körüli háromszögnormálok átlagolása."""
    # vertices: Nx3 list/array, index = x + y*size
    verts = np.array(vertices, dtype=np.float32).reshape((size, size, 3))
    normals = np.zeros_like(verts)
    # sobel-like gradient
    for y in range(1, size-1):
        for x in range(1, size-1):
            dzdx = (verts[y, x+1, 2] - verts[y, x-1, 2]) * 0.5
            dzdy = (verts[y+1, x, 2] - verts[y-1, x, 2]) * 0.5
            n = np.array([-dzdx, -dzdy, 1.0], dtype=np.float32)
            n /= np.linalg.norm(n) + 1e-9
            normals[y, x] = n
    # edge fallback
    normals[0,:,:] = normals[1,:,:]
    normals[-1,:,:] = normals[-2,:,:]
    normals[:,0,:] = normals[:,1,:]
    normals[:,-1,:] = normals[:,-2,:]
    return normals.reshape((-1,3))

def create_geom_from_heightmap(heightmap, scale_x=1.0, scale_y=1.0, scale_z=1.0):
    size = heightmap.shape[0]
    fmt = GeomVertexFormat.getV3n3t2()
    vdata = GeomVertexData("island", fmt, Geom.UHStatic)
    vwriter = GeomVertexWriter(vdata, "vertex")
    nwriter = GeomVertexWriter(vdata, "normal")
    twriter = GeomVertexWriter(vdata, "texcoord")
    vertices = []
    for y in range(size):
        for x in range(size):
            z = float(heightmap[y, x]) * scale_z
            vx = (x - size//2) * scale_x
            vy = (y - size//2) * scale_y
            vwriter.addData3(vx, vy, z)
            vertices.append((vx, vy, z))
            twriter.addData2(x / (size-1), y / (size-1))
            nwriter.addData3(0,0,1)  # ideiglenes

    # indexek
    tris = GeomTriangles(Geom.UHStatic)
    for y in range(size-1):
        for x in range(size-1):
            i = x + y * size
            tris.addVertices(i, i + 1, i + size)
            tris.addVertices(i + 1, i + size + 1, i + size)

    # normálok számítása és beírása
    normals = compute_normals(vertices, size)
    # át kell írni a normal channelt (vdata átírás)
    nreader = GeomVertexReader(vdata, "normal")
    # reset és overwrite (kicsit alacsony szint)
    nwriter = GeomVertexWriter(vdata, "normal")
    for i in range(len(normals)):
        nwriter.setRow(i)
        nwriter.setData3(normals[i,0], normals[i,1], normals[i,2])

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode("island")
    node.addGeom(geom)
    return node

def make_island_nodepath(base, heightmap, pos=(0,0,0), scale=(1,1,1)):
    node = create_geom_from_heightmap(heightmap, scale_x=scale[0], scale_y=scale[1], scale_z=scale[2])
    np_node = NodePath(node)
    np_node.setPos(*pos)
    # egyszerű shader/textúra lehet itt beállítva
    # példa: alap shader betöltése ha létezik shaders/island.frag/vert
    try:
        sh = Shader.load(Shader.SL_GLSL, "shaders/island.vert", "shaders/island.frag")
        np_node.setShader(sh)
    except Exception:
        pass
    return np_node
