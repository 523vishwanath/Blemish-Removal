"""
=============================================================
  Blemish Removal — Interactive Skin Retouching with OpenCV
=============================================================
  Author  : Vishwanath Reddy
  Tech    : Python · OpenCV · NumPy
  Usage   : python blemish_removal.py
  Controls: Left-click a blemish to remove it | ESC to quit
=============================================================
"""

import cv2
import numpy as np
import sys
import os

# ──────────────────────────────────────────────
#  CONFIG — update the path to your image here
# ──────────────────────────────────────────────
IMAGE_PATH = "images/blemish.png"
PATCH_RADIUS = 15          # radius (px) of the blemish patch
WINDOW_NAME = "Blemish Removal"


# ──────────────────────────────────────────────
#  GLOBAL STATE
# ──────────────────────────────────────────────
image = None          # current working image (mutated on each click)
history = []          # stack of previous images for undo (key: 'u')


# ──────────────────────────────────────────────
#  CORE: Sobel gradient analysis
# ──────────────────────────────────────────────
def compute_gradient(patch):
    """
    Returns the mean absolute Sobel gradient (X, Y) for a patch.
    Lower values indicate smoother / more skin-like texture.
    """
    if patch is None or patch.size == 0:
        return float("inf"), float("inf")

    sobel_x = cv2.Sobel(patch, cv2.CV_64F, 1, 0)
    sobel_y = cv2.Sobel(patch, cv2.CV_64F, 0, 1)

    mean_x = np.mean(np.abs(sobel_x))
    mean_y = np.mean(np.abs(sobel_y))
    return mean_x, mean_y


# ──────────────────────────────────────────────
#  CORE: Find best replacement patch
# ──────────────────────────────────────────────
def find_best_patch(cx, cy):
    """
    Samples 4 candidate patches in the neighbourhood of (cx, cy):
      right, left, above, below — each at distance 2r.
    Selects the one with the lowest mean X-gradient (smoothest skin).

    Returns (patch_x, patch_y) — top-left corner of the best patch.
    """
    r = PATCH_RADIUS
    h, w = image.shape[:2]

    candidates = {
        "right":  (cx + 2 * r, cy),
        "left":   (cx - 2 * r, cy),
        "above":  (cx,         cy - 2 * r),
        "below":  (cx,         cy + 2 * r),
    }

    best_key = None
    best_grad = float("inf")

    for key, (px, py) in candidates.items():
        # Bounds check — skip if patch would fall outside the image
        if px < 0 or py < 0 or px + 2 * r > w or py + 2 * r > h:
            continue

        patch = image[py: py + 2 * r, px: px + 2 * r]
        gx, _ = compute_gradient(patch)

        if gx < best_grad:
            best_grad = gx
            best_key = key

    if best_key is None:
        return None, None   # no valid patch found (edge of image)

    return candidates[best_key]


# ──────────────────────────────────────────────
#  CORE: Apply seamless blemish removal
# ──────────────────────────────────────────────
def remove_blemish(cx, cy):
    """
    Replaces the blemish centred at (cx, cy) with the best nearby
    skin patch using Poisson seamless cloning for a natural blend.
    """
    global image

    px, py = find_best_patch(cx, cy)
    if px is None:
        print(f"  ⚠  No valid patch found near ({cx}, {cy}) — too close to image edge.")
        return

    r = PATCH_RADIUS
    source = image[py: py + 2 * r, px: px + 2 * r]

    # Full-white mask → clone the entire patch
    mask = 255 * np.ones(source.shape, dtype=source.dtype)

    # seamlessClone expects the centre of the destination region
    centre = (cx, cy)
    image = cv2.seamlessClone(source, image, mask, centre, cv2.NORMAL_CLONE)

    print(f"  ✔  Blemish at ({cx}, {cy}) removed using patch from ({px}, {py})")


# ──────────────────────────────────────────────
#  MOUSE CALLBACK
# ──────────────────────────────────────────────
def on_mouse(event, x, y, flags, param):
    global image, history

    if event == cv2.EVENT_LBUTTONDOWN:
        # Save current state to history before modifying
        history.append(image.copy())

        remove_blemish(x, y)
        cv2.imshow(WINDOW_NAME, image)


# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────
def main():
    global image

    # ── Load image ──────────────────────────────
    if not os.path.exists(IMAGE_PATH):
        print(f"[ERROR] Image not found: '{IMAGE_PATH}'")
        print("        Update IMAGE_PATH at the top of this script.")
        sys.exit(1)

    image = cv2.imread(IMAGE_PATH)
    if image is None:
        print(f"[ERROR] cv2.imread failed for '{IMAGE_PATH}'.")
        sys.exit(1)

    print("=" * 52)
    print("  Blemish Removal")
    print("=" * 52)
    print(f"  Image  : {IMAGE_PATH}")
    print(f"  Size   : {image.shape[1]}×{image.shape[0]} px")
    print(f"  Radius : {PATCH_RADIUS} px")
    print()
    print("  Left-click  →  remove blemish")
    print("  U           →  undo last removal")
    print("  S           →  save result to 'images/result.png'")
    print("  ESC         →  quit")
    print("=" * 52)

    # ── Window & callback ───────────────────────
    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse)

    # ── Event loop ──────────────────────────────
    while True:
        cv2.imshow(WINDOW_NAME, image)
        key = cv2.waitKey(20) & 0xFF

        # ESC → quit
        if key == 27:
            print("\n  Exiting. Goodbye!")
            break

        # U → undo
        elif key == ord("u"):
            if history:
                image = history.pop()
                cv2.imshow(WINDOW_NAME, image)
                print("  ↩  Undo applied.")
            else:
                print("  ⚠  Nothing to undo.")

        # S → save
        elif key == ord("s"):
            out_path = "images/result.png"
            os.makedirs("images", exist_ok=True)
            cv2.imwrite(out_path, image)
            print(f"  💾  Result saved to '{out_path}'")

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
