import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Create a sample data array
data = np.random.rand(10, 10)

# Create a function to update the imshow plot
def update_plot():
    vmin = vmin_var.get()
    vmax = vmax_var.get()
    ax.clear()
    ax.imshow(data, cmap='viridis', vmin=vmin, vmax=vmax)
    ax.set_title(f"Vmin: {vmin}, Vmax: {vmax}")
    canvas.draw()

# Create a tkinter window
root = tk.Tk()
root.title("imshow Control")

# Create variables to store vmin and vmax values
vmin_var = tk.DoubleVar()
vmax_var = tk.DoubleVar()
vmin_var.set(0)  # Initial vmin
vmax_var.set(1)  # Initial vmax

# Create labels and sliders for vmin and vmax
vmin_label = tk.Label(root, text="Vmin:")
vmax_label = tk.Label(root, text="Vmax:")
vmin_slider = tk.Scale(root, from_=0, to=1, resolution=0.01, orient="horizontal", variable=vmin_var, command=update_plot)
vmax_slider = tk.Scale(root, from_=0, to=1, resolution=0.01, orient="horizontal", variable=vmax_var, command=update_plot)

# Create a Matplotlib figure
fig, ax = plt.subplots()
ax.imshow(data, cmap='viridis', vmin=vmin_var.get(), vmax=vmax_var.get())
ax.set_title(f"Vmin: {vmin_var.get()}, Vmax: {vmax_var.get()}")

# Embed the Matplotlib figure in the tkinter window
canvas = FigureCanvasTkAgg(fig, master=root)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack()

# Place labels and sliders in the tkinter window
vmin_label.pack()
vmin_slider.pack()
vmax_label.pack()
vmax_slider.pack()

# Start the tkinter main loop
root.mainloop()
