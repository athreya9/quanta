import math
from PIL import Image, ImageDraw

def draw_quanta_logo(size):
    # Create image with high resolution for anti-aliasing
    scale = 4
    canvas_size = size * scale
    img = Image.new("RGBA", (canvas_size, canvas_size), (11, 16, 32, 255))
    draw = ImageDraw.Draw(img)

    # Rounded background container
    corner_radius = int(canvas_size * 0.2)
    draw.rounded_rectangle(
        [0, 0, canvas_size - 1, canvas_size - 1],
        radius=corner_radius,
        fill=(11, 16, 32, 255),
        outline=(0, 240, 255, 120),
        width=int(canvas_size * 0.03)
    )

    # Infinity loop parameters
    cx = canvas_size / 2
    cy = canvas_size / 2
    a = canvas_size * 0.30  # Scale factor for lemniscate of Bernoulli
    stroke_width = max(2, int(canvas_size * 0.08))

    points = []
    num_samples = 400
    for i in range(num_samples):
        t = (2 * math.pi * i) / num_samples
        # Lemniscate formula: x = a * cos(t) / (1 + sin^2(t)), y = a * sin(t) * cos(t) / (1 + sin^2(t))
        denom = 1 + math.sin(t) ** 2
        x = cx + (a * math.cos(t)) / denom
        y = cy + (a * math.sin(t) * math.cos(t)) / denom
        points.append((x, y, t))

    # Draw gradient infinity curve
    for i in range(len(points)):
        p1 = points[i]
        p2 = points[(i + 1) % len(points)]

        # Calculate color gradient: left side (#00F0FF blue) -> right side (#FF9900 golden-orange)
        # Normalize x position relative to cx
        norm_x = (p1[0] - (cx - a)) / (2 * a)
        norm_x = max(0.0, min(1.0, norm_x))

        r = int(0 * (1 - norm_x) + 255 * norm_x)
        g = int(240 * (1 - norm_x) + 153 * norm_x)
        b = int(255 * (1 - norm_x) + 0 * norm_x)

        draw.line([p1[0], p1[1], p2[0], p2[1]], fill=(r, g, b, 255), width=stroke_width)

    # Downscale for crisp anti-aliasing
    return img.resize((size, size), Image.Resampling.LANCZOS)

for sz in [16, 48, 128]:
    icon = draw_quanta_logo(sz)
    icon.save(f"chrome-extension/icon{sz}.png")
    print(f"Generated chrome-extension/icon{sz}.png ({sz}x{sz})")
