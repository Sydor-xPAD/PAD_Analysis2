from ij import IJ
from ij.gui import Roi, Plot
from java.awt import Color

imp = IJ.getImage()

# Check image dimensions
if imp.getWidth() != 512 or imp.getHeight() != 512 or imp.getStackSize() != 500:
    IJ.showMessage("Error", "Image must be 512x512x500")
    exit()

# List of colors for up to 16 ROIs
colors = [
    Color.RED, Color.BLUE, Color.GREEN, Color.MAGENTA,
    Color.ORANGE, Color.CYAN, Color.PINK, Color.YELLOW,
    Color.GRAY, Color.DARK_GRAY, Color.LIGHT_GRAY, Color.BLACK,
    Color(128,0,0), Color(0,128,0), Color(0,0,128), Color(128,128,0)
]

plot = None
roi_labels = []
roi_width = 100
roi_height = 100

for m in range(16):
    sx = (m % 4) * 128
    sy = (m // 4) * 128
    roi = Roi(sx + 14, sy + 14, 100, 100)
    imp.setRoi(roi)
    
    means = []
    frames = []

    for i in range(imp.getStackSize()):
        imp.setSlice(i + 1)
        ip = imp.getProcessor()
        
        # Get the entire pixel array for the slice (float array for 32-bit images)
        pixels = ip.getPixels()
        
        # Extract ROI pixels by indexing into the 1D pixel array
        roi_pixels = []
        for y in range(sy, sy + roi_height):
            offset = y * imp.getWidth() + sx
            # Get a slice of pixels for this row in ROI
            row_pixels = pixels[offset:offset + roi_width]
            roi_pixels.extend(row_pixels)
        
        # Compute mean and stddev
        n = len(roi_pixels)
        mean = sum(roi_pixels) / float(n)
        variance = sum((p - mean) ** 2 for p in roi_pixels) / float(n)
        stddev = variance ** 0.5
        
        # Filter out pixels > mean + 4*stddev
        filtered = [p for p in roi_pixels if p <= mean + 4*stddev]
        if filtered:
            clipped_mean = sum(filtered) / float(len(filtered))
        else:
            clipped_mean = mean
        
        means.append(clipped_mean)
        frames.append(i + 1)
      
    
    if m == 0:
        # Create plot with first series
        plot = Plot("Mean Intensity Over Time (All ROIs)", "Frame", "Mean", frames, means)
        plot.setColor(colors[m])
    else:
        plot.setColor(colors[m])
        plot.add("line", frames, means)
    roi_labels.append("roi%d" % m)

# Add legend with all ROI labels
plot.addLegend("\n".join(roi_labels))
plot.show()
