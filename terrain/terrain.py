import numpy as np
import math
from panda3d.core import (
    Geom, GeomNode, GeomTriangles, GeomVertexFormat,
    GeomVertexWriter, GeomVertexData, NodePath,
    GeomVertexReader, Shader
)

# --- Segédfüggvények (Normál számítás) ---
def compute_normals(vertices, size):
    """Normál vektorok számítása a domborzathoz (Négyzetes rácshoz)."""
    verts = np.array(vertices, dtype=np.float32).reshape((size, size, 3))
    normals = np.zeros_like(verts)
    
    for y in range(1, size-1):
        for x in range(1, size-1):
            dzdx = (verts[y, x+1, 2] - verts[y, x-1, 2]) * 0.5
            dzdy = (verts[y+1, x, 2] - verts[y-1, x, 2]) * 0.5
            n = np.array([-dzdx, -dzdy, 1.0], dtype=np.float32)
            norm_len = np.linalg.norm(n)
            if norm_len > 0:
                n /= norm_len
            normals[y, x] = n
            
    normals[0,:,:] = normals[1,:,:]
    normals[-1,:,:] = normals[-2,:,:]
    normals[:,0,:] = normals[:,1,:]
    normals[:,-1,:] = normals[:,-2,:]
    
    return normals.reshape((-1,3))

# --- Eredeti Négyzetes Generáló ---
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
            nwriter.addData3(0,0,1)

    tris = GeomTriangles(Geom.UHStatic)
    for y in range(size-1):
        for x in range(size-1):
            i = x + y * size
            tris.addVertices(i, i + 1, i + size)
            tris.addVertices(i + 1, i + size + 1, i + size)

    normals = compute_normals(vertices, size)
    nwriter = GeomVertexWriter(vdata, "normal")
    for i in range(len(normals)):
        nwriter.setData3(normals[i,0], normals[i,1], normals[i,2])

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode("island")
    node.addGeom(geom)
    return node

# --- ÚJ: Körkörös (Radiális) Generáló ---
def create_radial_geom(heightmap, radius=100, rings=64, segments=64, height_scale=10.0):
    """
    Kör alapú geometriát készít (mint egy pókháló).
    heightmap: A magassági adatok (2D array)
    radius: A sziget sugara a világban
    rings: Hány koncentrikus körből álljon
    segments: Hány cikkelyre legyen osztva egy kör
    """
    size = heightmap.shape[0] # Feltételezzük, hogy négyzetes a heightmap
    
    fmt = GeomVertexFormat.getV3n3t2()
    vdata = GeomVertexData("radial_island", fmt, Geom.UHStatic)
    
    vwriter = GeomVertexWriter(vdata, "vertex")
    nwriter = GeomVertexWriter(vdata, "normal")
    twriter = GeomVertexWriter(vdata, "texcoord")
    
    # 1. Középpont (index 0)
    # A heightmap közepéről vesszük a magasságot
    center_z = float(heightmap[size//2, size//2]) * height_scale
    vwriter.addData3(0, 0, center_z)
    nwriter.addData3(0, 0, 1) # Ideiglenes normál felfelé
    twriter.addData2(0.5, 0.5)
    
    # 2. Gyűrűk generálása
    for r in range(1, rings + 1):
        r_ratio = r / rings # 0..1 (milyen messze vagyunk a középponttól)
        current_radius = r_ratio * radius
        
        for s in range(segments):
            angle = (s / segments) * 2 * math.pi
            
            # X, Y koordináták
            x = math.cos(angle) * current_radius
            y = math.sin(angle) * current_radius
            
            # UV koordináták (hogy kiolvassuk a heightmapből az adatot)
            # A (0,0) pont a térkép (0.5, 0.5) pontja
            u = 0.5 + (math.cos(angle) * r_ratio * 0.5)
            v = 0.5 + (math.sin(angle) * r_ratio * 0.5)
            
            # Heightmap pixel index
            hm_x = int(min(size - 1, max(0, u * size)))
            hm_y = int(min(size - 1, max(0, v * size)))
            
            z = float(heightmap[hm_y, hm_x]) * height_scale
            
            vwriter.addData3(x, y, z)
            nwriter.addData3(0, 0, 1) # Normálok számítása itt bonyolultabb, most hagyjuk felfelé
            twriter.addData2(u, v)

    # 3. Háromszögelés
    tris = GeomTriangles(Geom.UHStatic)
    
    # A) Belső kör (Középpont összekötése az első gyűrűvel)
    for s in range(segments):
        next_s = (s + 1) % segments
        # 0: középpont
        # 1..segments: első gyűrű pontjai
        tris.addVertices(0, s + 1, next_s + 1)
        
    # B) Többi gyűrű
    for r in range(rings - 1):
        # Az aktuális gyűrű kezdő indexe a vertex listában
        # +1, mert a 0. index a középpont
        row_start = 1 + r * segments
        next_row_start = 1 + (r + 1) * segments
        
        for s in range(segments):
            next_s = (s + 1) % segments
            
            curr_p = row_start + s
            curr_next_p = row_start + next_s
            
            upper_p = next_row_start + s
            upper_next_p = next_row_start + next_s
            
            # Két háromszög alkot egy négyszöget két gyűrű között
            tris.addVertices(curr_p, upper_next_p, upper_p)
            tris.addVertices(curr_p, curr_next_p, upper_next_p)

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode("radial_island")
    node.addGeom(geom)
    return node

# --- NodePath Létrehozók ---

def make_island_nodepath(base, heightmap, pos=(0,0,0), scale=(1,1,1)):
    """A régi négyzetes módszer."""
    node = create_geom_from_heightmap(heightmap, scale_x=scale[0], scale_y=scale[1], scale_z=scale[2])
    np_node = NodePath(node)
    np_node.setPos(*pos)
    return np_node

def make_radial_island_nodepath(base, heightmap, pos=(0,0,0), radius=100, height_scale=20.0):
    """AZ ÚJ körkörös módszer hívása."""
    # Itt fixálhatjuk a gyűrűk számát, vagy átadhatjuk paraméterként
    node = create_radial_geom(heightmap, radius=radius, rings=64, segments=64, height_scale=height_scale)
    np_node = NodePath(node)
    np_node.setPos(*pos)
    return np_node