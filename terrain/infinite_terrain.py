import math
import random
from panda3d.core import (
    Geom, GeomNode, GeomVertexData, GeomVertexFormat, GeomVertexArrayFormat,
    GeomVertexWriter, GeomTriangles, NodePath, InternalName,
    Vec3, Shader, BitMask32
)

class InfiniteTerrain:
    def __init__(self, render_node, seed=42):
        self.render_node = render_node
        # Létrehozunk egy gyökér node-ot a terepnek
        self.root = self.render_node.attachNewNode("infinite_terrain_root")
        
        # Ütközési maszk (hogy a PhysicsManager és az AI lássa a talajt)
        # A BitMask32.bit(1) a TERRAIN maszkja a physics.py szerint
        self.terrain_mask = BitMask32.bit(1)
        
        # Hullám paraméterek
        random.seed(seed)
        self.waves = []
        for _ in range(4):
            self.waves.append({
                'amp': random.uniform(1.0, 5.0),
                'freq_x': random.uniform(0.05, 0.2), 
                'freq_y': random.uniform(0.05, 0.2),
                'phase_x': random.uniform(0, math.pi),
                'phase_y': random.uniform(0, math.pi)
            })
            
        # Konfiguráció
        self.chunk_size = 32
        self.quad_size = 2.0
        self.chunk_world_size = (self.chunk_size - 1) * self.quad_size 
        self.render_distance = 2 
        self.active_chunks = {}

        # Vertex formátum és Shader beállítása
        self.setup_vertex_format()
        self.setup_shader()
        
        # Kezdeti generálás a (0,0) pont körül
        self.update(Vec3(0,0,0))

    def setup_vertex_format(self):
        """Egyedi formátum a normálokhoz, tangensekhez."""
        format_array = GeomVertexArrayFormat()
        format_array.addColumn(InternalName.getVertex(), 3, Geom.NT_float32, Geom.C_point)
        format_array.addColumn(InternalName.getNormal(), 3, Geom.NT_float32, Geom.C_vector)
        format_array.addColumn(InternalName.getTexcoord(), 2, Geom.NT_float32, Geom.C_texcoord)
        format_array.addColumn(InternalName.getTangent(), 3, Geom.NT_float32, Geom.C_vector)
        format_array.addColumn(InternalName.getBinormal(), 3, Geom.NT_float32, Geom.C_vector)
        
        self.custom_format = GeomVertexFormat()
        self.custom_format.addArray(format_array)
        self.custom_format = GeomVertexFormat.registerFormat(self.custom_format)

    def get_height_slope(self, x, y):
        """Matematikai magasság számítás."""
        z = 0.0
        slope_x = 0.0
        slope_y = 0.0

        for wave in self.waves:
            val_x = x * wave['freq_x'] + wave['phase_x']
            val_y = y * wave['freq_y'] + wave['phase_y']
            
            sx = math.sin(val_x); cx = math.cos(val_x)
            sy = math.sin(val_y); cy = math.cos(val_y)
            
            z += wave['amp'] * sx * cy
            slope_x += wave['amp'] * wave['freq_x'] * cx * cy
            slope_y += wave['amp'] * wave['freq_y'] * sx * (-sy)

        return z, slope_x, slope_y

    def generate_chunk(self, cx, cy):
        """Egy chunk geometriájának legenerálása."""
        vdata = GeomVertexData(f'chunk_{cx}_{cy}', self.custom_format, Geom.UH_static)
        vdata.setNumRows(self.chunk_size * self.chunk_size)

        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        texcoord = GeomVertexWriter(vdata, 'texcoord')
        tangent = GeomVertexWriter(vdata, 'tangent')
        binormal = GeomVertexWriter(vdata, 'binormal')

        start_x = cx * self.chunk_world_size
        start_y = cy * self.chunk_world_size

        for y in range(self.chunk_size):
            for x in range(self.chunk_size):
                px = start_x + x * self.quad_size
                py = start_y + y * self.quad_size
                
                pz, slope_x, slope_y = self.get_height_slope(px, py)

                tan_vec = Vec3(1, 0, slope_x); tan_vec.normalize()
                bi_vec = Vec3(0, 1, slope_y); bi_vec.normalize()
                norm_vec = tan_vec.cross(bi_vec); norm_vec.normalize()

                vertex.addData3f(px, py, pz)
                normal.addData3f(norm_vec)
                texcoord.addData2f(px * 0.2, py * 0.2)
                tangent.addData3f(tan_vec)
                binormal.addData3f(bi_vec)

        tris = GeomTriangles(Geom.UH_static)
        for y in range(self.chunk_size - 1):
            for x in range(self.chunk_size - 1):
                i0 = y * self.chunk_size + x
                i1 = i0 + 1
                i2 = (y + 1) * self.chunk_size + x
                i3 = i2 + 1
                tris.addVertices(i0, i1, i2)
                tris.addVertices(i1, i3, i2)

        geom = Geom(vdata)
        geom.addPrimitive(tris)
        node = GeomNode(f'chunk_node_{cx}_{cy}')
        node.addGeom(geom)
        
        np = self.root.attachNewNode(node)
        
        # JAVÍTÁS: NodePath esetén a helyes metódus 'setCollideMask'.
        # Ez beállítja az "into" maszkot a node-on, így a sugarak eltalálják.
        np.setCollideMask(self.terrain_mask)
        
        return np

    def update(self, player_pos):
        """Chunkok betöltése/kitétele a játékos pozíciója alapján."""
        p_cx = int(math.floor(player_pos.x / self.chunk_world_size))
        p_cy = int(math.floor(player_pos.y / self.chunk_world_size))

        needed_chunks = set()
        rng = self.render_distance
        for x in range(p_cx - rng, p_cx + rng + 1):
            for y in range(p_cy - rng, p_cy + rng + 1):
                needed_chunks.add((x, y))

        for key in list(self.active_chunks.keys()):
            if key not in needed_chunks:
                self.active_chunks[key].removeNode()
                del self.active_chunks[key]

        for key in needed_chunks:
            if key not in self.active_chunks:
                self.active_chunks[key] = self.generate_chunk(key[0], key[1])

    def setup_shader(self):
        vert_shader = """
        #version 150
        in vec4 p3d_Vertex;
        in vec3 p3d_Normal;
        in vec2 p3d_MultiTexCoord0;
        uniform mat4 p3d_ModelViewProjectionMatrix;
        uniform mat3 p3d_NormalMatrix;
        out vec3 normal;
        out vec3 worldPos;
        out vec2 texcoord;

        void main() {
            gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
            worldPos = p3d_Vertex.xyz;
            normal = normalize(p3d_NormalMatrix * p3d_Normal);
            texcoord = p3d_MultiTexCoord0;
        }
        """

        frag_shader = """
        #version 150
        in vec3 normal;
        in vec3 worldPos;
        in vec2 texcoord;
        out vec4 p3d_FragColor;

        void main() {
            vec3 N = normalize(normal);
            float grid = 0.0;
            if (fract(texcoord.x) < 0.02 || fract(texcoord.y) < 0.02) grid = 0.1;
            
            vec3 baseColor = vec3(0.2, 0.6, 0.3);
            if (worldPos.z > 3.0) baseColor = vec3(0.5, 0.5, 0.5);
            if (worldPos.z > 5.5) baseColor = vec3(0.9, 0.9, 0.9);
            if (worldPos.z < -1.0) baseColor = vec3(0.7, 0.6, 0.4);
            
            vec3 lightDir = normalize(vec3(0.5, 0.5, 1.0));
            float diff = max(dot(N, lightDir), 0.2);
            
            p3d_FragColor = vec4(baseColor * diff + vec3(grid), 1.0);
        }
        """
        shader = Shader.make(Shader.SL_GLSL, vert_shader, frag_shader)
        self.root.setShader(shader)