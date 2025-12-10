import numpy as np
from panda3d.core import (
    Geom, GeomNode, GeomTriangles, GeomVertexFormat,
    GeomVertexWriter, GeomVertexData, NodePath,
    GeomVertexReader, Shader
)

def compute_normals(vertices, size):
    """Normál vektorok számítása a domborzathoz."""
    # vertices: Nx3 array
    verts = np.array(vertices, dtype=np.float32).reshape((size, size, 3))
    normals = np.zeros_like(verts)
    
    # Sobel-szerű gradiens számítás a szomszédok alapján
    for y in range(1, size-1):
        for x in range(1, size-1):
            # Keresztirányú vektorok (differencia)
            dzdx = (verts[y, x+1, 2] - verts[y, x-1, 2]) * 0.5
            dzdy = (verts[y+1, x, 2] - verts[y-1, x, 2]) * 0.5
            
            # Normálvektor: (-dz/dx, -dz/dy, 1) normalizálva
            n = np.array([-dzdx, -dzdy, 1.0], dtype=np.float32)
            norm_len = np.linalg.norm(n)
            if norm_len > 0:
                n /= norm_len
            normals[y, x] = n
            
    # Szélek kezelése (másolás a belső szomszédról)
    normals[0,:,:] = normals[1,:,:]
    normals[-1,:,:] = normals[-2,:,:]
    normals[:,0,:] = normals[:,1,:]
    normals[:,-1,:] = normals[:,-2,:]
    
    return normals.reshape((-1,3))

def create_geom_from_heightmap(heightmap, scale_x=1.0, scale_y=1.0, scale_z=1.0):
    size = heightmap.shape[0]
    
    # Formátum: Vertex + Normal + Texcoord
    fmt = GeomVertexFormat.getV3n3t2()
    vdata = GeomVertexData("island", fmt, Geom.UHStatic)
    
    vwriter = GeomVertexWriter(vdata, "vertex")
    nwriter = GeomVertexWriter(vdata, "normal")
    twriter = GeomVertexWriter(vdata, "texcoord")
    
    vertices = []
    
    # 1. Csúcspontok létrehozása
    for y in range(size):
        for x in range(size):
            z = float(heightmap[y, x]) * scale_z
            # Középre igazítás (size/2)
            vx = (x - size//2) * scale_x
            vy = (y - size//2) * scale_y
            
            vwriter.addData3(vx, vy, z)
            vertices.append((vx, vy, z))
            
            # UV koordináták 0..1 között
            twriter.addData2(x / (size-1), y / (size-1))
            
            # Ideiglenes normál (felfelé mutat)
            nwriter.addData3(0,0,1)

    # 2. Háromszögek (Triangles) létrehozása
    tris = GeomTriangles(Geom.UHStatic)
    for y in range(size-1):
        for x in range(size-1):
            # Indexek a rácsban
            i = x + y * size
            # Két háromszög alkot egy négyzetet (quad)
            tris.addVertices(i, i + 1, i + size)
            tris.addVertices(i + 1, i + size + 1, i + size)

    # 3. Normálok utólagos számítása a szép árnyékoláshoz
    normals = compute_normals(vertices, size)
    
    # Visszaírás a GeomVertexData-ba
    # Új writer kell a reseteléshez/felülíráshoz
    nwriter = GeomVertexWriter(vdata, "normal")
    for i in range(len(normals)):
        nwriter.setData3(normals[i,0], normals[i,1], normals[i,2])

    # Geom összeállítása
    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode("island")
    node.addGeom(geom)
    return node

def make_island_nodepath(base, heightmap, pos=(0,0,0), scale=(1,1,1)):
    """NodePath létrehozása és opcionális shader beállítása."""
    node = create_geom_from_heightmap(heightmap, scale_x=scale[0], scale_y=scale[1], scale_z=scale[2])
    np_node = NodePath(node)
    np_node.setPos(*pos)
    
    # Itt lehetne shadert betölteni, ha van
    # sh = Shader.load(...)
    
    return np_node