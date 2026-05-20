import numpy as np
import matplotlib.pyplot as plt
from ipywidgets import interact, FloatSlider

# Create some example data
data = np.random.rand(10, 10)

# Create a function to update the imshow plot
def update_plot(vmin, vmax):
    plt.imshow(data, cmap='viridis', vmin=vmin, vmax=vmax)
    plt.colorbar()

# Create sliders for vmin and vmax
vmin_slider = FloatSlider(min=0, max=1, step=0.01, description='Vmin', value=0)
vmax_slider = FloatSlider(min=0, max=1, step=0.01, description='Vmax', value=1)

# Define an interactive widget to update the plot
interact(update_plot, vmin=vmin_slider, vmax=vmax_slider)

# Show the initial plot
update_plot(vmin_slider.value, vmax_slider.value)

# Display the sliders
vmin_slider, vmax_slider
