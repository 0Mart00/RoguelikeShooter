import numpy as np
from noise import pnoise2
from scipy.signal import convolve2d

def fbm_noise(size, scale=6.0, octaves=5, lacunarity=2.0, gain=0.5, seed=0):
    """Fractal Brownian Motion 2D heightmap (NumPy tömböt ad)."""
    rng = np.random.RandomState(seed)
    base_x = rng.randint(0, 10000)
    base_y = rng.randint(0, 10000)
    
    # Koordináta rács létrehozása
    xs = np.linspace(0, scale, size, endpoint=False)
    ys = np.linspace(0, scale, size, endpoint=False)
    
    # Meshgrid a zajhoz
    # Fontos: a pnoise2 C-alapú és lassú lehet Python loopban, 
    # de kis méretnél (129x129) elfogadható.
    heightmap = np.zeros((size, size), dtype=np.float32)
    
    for i in range(size):
        for j in range(size):
            # Több oktáv összeadása
            amp = 1.0
            freq = 1.0
            val = 0.0
            for _ in range(octaves):
                val += amp * pnoise2(
                    (base_x + xs[i]) * freq, 
                    (base_y + ys[j]) * freq
                )
                amp *= gain
                freq *= lacunarity
            heightmap[i, j] = val

    # Normalizálás 0..1 közé
    mn, mx = heightmap.min(), heightmap.max()
    heightmap = (heightmap - mn) / (mx - mn + 1e-9)
    return heightmap

def island_mask(size, radius_factor=0.9, exponent=2.5):
    """Kör alakú maszk: középen 1, szélén 0."""
    cx = (size - 1) / 2.0
    cy = (size - 1) / 2.0
    y, x = np.ogrid[0:size, 0:size]
    
    # Távolság a középponttól
    dx = (x - cx) / (cx * radius_factor)
    dy = (y - cy) / (cy * radius_factor)
    dist = np.sqrt(dx*dx + dy*dy)
    
    # Vágás és hatványozás a lecsengéshez
    m = np.clip(1.0 - dist**exponent, 0.0, 1.0)
    return m.astype(np.float32)

def generate_island(size=129, height_scale=30.0, seed=0):
    """Visszaadja a végső heightmap-ot (size x size) lebegő szigethez."""
    # 1. Alap zaj generálása
    noise = fbm_noise(size=size, scale=4.0, octaves=6, seed=seed)
    
    # 2. Maszk létrehozása (sziget forma)
    mask = island_mask(size=size, radius_factor=0.95, exponent=2.8)
    
    # 3. Maszkolás (középen magas, szélen nulla)
    falloff = mask**1.2
    heightmap = noise * falloff
    
    # 4. Simítás (Blur) a durva élek ellen
    kernel = np.array([[1,2,1],[2,4,2],[1,2,1]], dtype=np.float32)
    kernel /= kernel.sum()
    heightmap = convolve2d(heightmap, kernel, mode='same', boundary='symm')
    
    # 5. Végső skálázás
    # Újra normalizáljuk, majd megszorozzuk a magassággal
    heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min() + 1e-9)
    heightmap *= height_scale
    
    return heightmap