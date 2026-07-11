"""
Render PNG tiles from pixel_data value grids.

Color scales replicate the Sentinel Hub evalscripts in
sentinel_hub_wms_service.py exactly, so DB-rendered tiles are
visually consistent with Sentinel Hub-rendered ones.
"""
import io
import logging

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

TILE_SIZE = 256

# {index: (thresholds, colors)} — value < thresholds[i] → colors[i],
# else colors[-1]. len(colors) == len(thresholds) + 1.
COLOR_SCALES = {
    'NDVI': (
        [-0.1, 0.0, 0.2, 0.4, 0.6],
        [(0.5, 0.3, 0.1), (0.8, 0.7, 0.4), (0.9, 0.9, 0.6),
         (0.6, 0.8, 0.3), (0.3, 0.7, 0.2), (0.1, 0.5, 0.1)]
    ),
    'NDWI': (
        [-0.5, -0.2, 0.0, 0.2, 0.5],
        [(0.5, 0.3, 0.1), (0.8, 0.7, 0.5), (0.5, 0.8, 0.9),
         (0.3, 0.5, 0.9), (0.0, 0.0, 0.8), (0.0, 0.0, 0.5)]
    ),
    'NDBI': (
        [-0.5, -0.2, 0.0, 0.2, 0.4],
        [(0.0, 0.0, 0.8), (0.1, 0.5, 0.1), (0.8, 0.7, 0.5),
         (0.6, 0.3, 0.1), (0.5, 0.2, 0.1), (0.5, 0.0, 0.0)]
    ),
    'MOISTURE': (
        [-0.8, -0.6, -0.4, -0.2, 0.0, 0.2],
        [(0.5, 0.0, 0.0), (0.8, 0.2, 0.2), (0.9, 0.5, 0.5), (1.0, 1.0, 0.0),
         (0.6, 0.9, 0.6), (0.0, 1.0, 1.0), (0.0, 0.0, 0.5)]
    ),
}


def render_grid_to_png(grid: np.ndarray, index_type: str) -> bytes:
    """
    Colorize a value grid (NaN = no data → transparent) and upscale
    to a 256x256 PNG tile.

    Expects grid row 0 = northernmost row (image orientation).
    """
    thresholds, colors = COLOR_SCALES[index_type.upper()]
    palette = np.array([[int(c * 255) for c in rgb] for rgb in colors], dtype=np.uint8)

    valid = np.isfinite(grid)
    # np.digitize maps value < thresholds[0] → 0 ... value >= thresholds[-1] → len(thresholds)
    bucket = np.digitize(np.nan_to_num(grid, nan=0.0), thresholds)

    rgba = np.zeros((*grid.shape, 4), dtype=np.uint8)
    rgba[..., :3] = palette[bucket]
    rgba[..., 3] = np.where(valid, 255, 0)

    img = Image.fromarray(rgba, 'RGBA').resize((TILE_SIZE, TILE_SIZE), Image.NEAREST)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def empty_tile_png() -> bytes:
    """Fully transparent 256x256 PNG (for tiles with no pixel data)"""
    buf = io.BytesIO()
    Image.new('RGBA', (TILE_SIZE, TILE_SIZE), (0, 0, 0, 0)).save(buf, format='PNG')
    return buf.getvalue()
