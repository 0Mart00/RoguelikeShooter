# terrain/generator.py
import numpy as np
from noise import pnoise2

def fbm_noise(size, scale=6.0, octaves=5, lacunarity=2.0, gain=0.5, seed=0):
    """Fractal Brownian Motion 2D heightmap (NumPy tömböt ad)."""
    rng = np.random.RandomState(seed)
    base_x = rng.randint(0, 10000)
    base_y = rng.randint(0, 10000)
    xs = np.linspace(0, scale, size, endpoint=False)
    ys = np.linspace(0, scale, size, endpoint=False)
    X, Y = np.meshgrid(xs + base_x, ys + base_y)
    Z = np.zeros((size, size), dtype=np.float32)
    amp = 1.0
    freq = 1.0
    for _ in range(octaves):
        for i in range(size):
            for j in range(size):
                Z[i, j] += amp * pnoise2(X[i, j] * freq, Y[i, j] * freq)
        amp *= gain
        freq *= lacunarity
    # normalize to 0..1
    Z = (Z - Z.min()) / (Z.max() - Z.min() + 1e-9)
    return Z

def island_mask(size, radius_factor=0.9, exponent=2.5):
    """Elliptic/round mask: középen 1, szélén 0. exponent szabályozza a peremen való lecsengést."""
    cx = (size - 1) / 2.0
    cy = (size - 1) / 2.0
    y, x = np.ogrid[0:size, 0:size]
    dx = (x - cx) / (cx * radius_factor)
    dy = (y - cy) / (cy * radius_factor)
    dist = np.sqrt(dx*dx + dy*dy)
    m = np.clip(1.0 - dist**exponent, 0.0, 1.0)
    return m.astype(np.float32)

def generate_island(size=129, height_scale=30.0, seed=0):
    """Visszaadja a végső heightmap-ot (size x size) lebegő szigethez."""
    noise = fbm_noise(size=size, scale=4.0, octaves=6, seed=seed)
    mask = island_mask(size=size, radius_factor=0.95, exponent=2.8)
    # szabályozzuk, hogy középen magas legyen, szélen karcsú
    falloff = mask**1.2
    heightmap = noise * falloff
    # simítás (gauss-szerű smoothing egyszerű konvolúcióval)
    kernel = np.array([[1,2,1],[2,4,2],[1,2,1]], dtype=np.float32)
    kernel /= kernel.sum()
    from scipy.signal import convolve2d
    heightmap = convolve2d(heightmap, kernel, mode='same', boundary='symm')
    # normalizálás és skálázás
    heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min() + 1e-9)
    heightmap *= height_scale
    return heightmap
