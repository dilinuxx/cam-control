import numpy as np
import cv2
import matplotlib.pyplot as plt
import tifffile as tiff

# ==============================================================================
# 1. DEFINE ENGINEERING CALIBRATION CONSTANTS
# ==============================================================================
# Spatial scale: How many micrometres (µm) fit into one pixel? 
# (Calibrate this using a micron ruler target placed inside your SLM chamber)
PIXEL_TO_MICRON = 4.2  

# Time scale: Frame-to-frame delta time (seconds)
# (Example: 10,000 frames per second = 1 / 10000 = 0.0001s)
DELTA_TIME = 0.0001  

# Simple Linear Calibration Mock: Counts to Celsius
# In practice, map this using Planck's Inversion: Temperature = f(Counts, Wavelength, Emissivity)
def counts_to_celsius(counts):
    # Ti-6Al-4V Liquidus Melting Temperature is approx 1650°C
    # We map sensor brightness values up to 65535 to physical temperatures
    base_temp = 20.0  # Ambient temperature
    temp_gradient = (2500.0 - 1650.0) / 65535.0
    return base_temp + (counts * temp_gradient)

# ==============================================================================
# 2. LOAD AND PROCESS THE SAMPLE IMAGE
# ==============================================================================
# Use tifffile to accurately preserve native 16-bit unsigned integers (0-65535)
try:
    # Native '.tiff' file path
    raw_img = tiff.imread('image10.tif')
except Exception:
    # Fallback to OpenCV if handling standard image arrays for testing
    raw_img = cv2.imread('image10.tif', cv2.IMREAD_UNCHANGED)

# Ensure image is single-channel grayscale
if len(raw_img.shape) == 3:
    raw_img = cv2.cvtColor(raw_img, cv2.COLOR_BGR2GRAY)

# ==============================================================================
# 3. COMPUTE METRIC A: MELT POOL GEOMETRY (WIDTH & LENGTH)
# ==============================================================================
# Convert raw array to estimated thermal scale
thermal_map = counts_to_celsius(raw_img)

# Isolate the melt pool boundary. Let's threshold for values near the melting point of Ti-64 (~1650°C)
# In raw intensity counts, let's look for pixels above a specific bright threshold.
# Adjust 'threshold_val' based on your background intensity profile.
threshold_val = int(raw_img.max() * 0.4) 
_, binary_mask = cv2.threshold(raw_img, threshold_val, 255, cv2.THRESH_BINARY)
binary_mask = binary_mask.astype(np.uint8)

# Extract contours from the isolated binary melt pool blob
contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

if contours:
    # Select the largest detected bright pool area
    melt_pool_contour = max(contours, key=cv2.contourArea)
    
    # Fit a minimum bounding rectangle to extract Length and Width independent of rotation angle
    rect = cv2.minAreaRect(melt_pool_contour)
    (x_center, y_center), (pixel_width, pixel_length), rotation_angle = rect
    
    # Convert pixel measurements into physical engineering dimensions (micrometres)
    physical_width_um = pixel_width * PIXEL_TO_MICRON
    physical_length_um = pixel_length * PIXEL_TO_MICRON
    
    print("--- Melt Pool Geometric Metrics ---")
    print(f"Melt Pool Width:  {physical_width_um:.2f} µm")
    print(f"Melt Pool Length: {physical_length_um:.2f} µm")
else:
    print("Warning: No melt pool structure detected above the intensity threshold.")
    physical_width_um, physical_length_um = 0, 0

# ==============================================================================
# 4. COMPUTE METRIC B: TEMPORAL COOLING RATES (MOCK SEQUENTIAL FRAME)
# ==============================================================================
# To simulate temporal cooling across a high-speed sequence, we compare current frame (t)
# against a simulated next frame (t + dt) where the thermal profile contracts/cools down.
simulated_next_frame = raw_img * 0.85  # Simulate a 15% drop in intensity as laser passes
thermal_map_next = counts_to_celsius(simulated_next_frame)

# Calculate Delta Temperature grid (dT)
delta_temperature = thermal_map_next - thermal_map

# Calculate Cooling Rate grid (dT / dt) in °C per second
cooling_rate_map = delta_temperature / DELTA_TIME

# Extract maximum cooling rate experienced near the localized heat zone
max_cooling_rate = np.abs(np.min(cooling_rate_map))
print("\n--- Melt Pool Thermal Dynamics ---")
print(f"Maximum Localized Cooling Rate: {max_cooling_rate:.2e} °C/s")

# ==============================================================================
# 5. VISUALIZATION AND REPORT DESIGN
# ==============================================================================
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Plot 1: Quantitative Thermal Profile Map
im1 = axes[0].imshow(thermal_map, cmap='inferno')
axes[0].set_title("Calibrated High-Res Thermal Profile Map")
fig.colorbar(im1, ax=axes[0], label="Estimated Temperature (°C)")

# Plot 2: Binary Boundary Mask Overlay
axes[1].imshow(binary_mask, cmap='gray')
axes[1].set_title("Melt Pool Boundary Isolation (Liquid-Solid Interface)")

plt.tight_layout()
plt.show()