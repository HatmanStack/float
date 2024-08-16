import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

import math

def modified_sigmoid(x, k=.005):
    return 1 / (1 + np.exp(-k * x))

def sigmoid(x):
  return 1 / (1 + np.exp(-x))

def tanh(x):
    return (np.exp(x) - np.exp(-x)) / (np.exp(x) + np.exp(-x))

def triangular_weights(num_colors, peak_index):
  x = np.arange(num_colors)
  weights = np.minimum(x, num_colors - x - 1)
  weights = weights / np.max(weights)
  return weights

def gaussian_weights(num_colors, mean, std):
  x = np.linspace(0, num_colors - 1, num_colors)
  weights = norm.pdf(x, loc=mean, scale=std)
  cumulative_weights = np.cumsum(weights)
  cumulative_weights /= cumulative_weights[-1]
  return cumulative_weights

def custom_weights(num_colors, peak_width):
  
  x = np.arange(num_colors)
  weights = np.abs(x - (num_colors - 1) / 2)
  weights = 1 - weights / max(weights)
  weights = weights ** peak_width

  return weights

def generate_color_gradient(start_hex, end_hex, num_colors):
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def rgb_to_hex(rgb):
        return '#{:02x}{:02x}{:02x}'.format(*rgb) 

    start_rgb = hex_to_rgb(start_hex)
    end_rgb = hex_to_rgb(end_hex)

    #color_steps = [(end_rgb[i] - start_rgb[i]) / (num_colors - 1) for i in range(3)]

    # Generate sigmoid weights
    x = np.linspace(-6, 6, num_colors)
    weights = sigmoid(x)
    #weights = modified_sigmoid(x)
    
    #weights = triangular_weights(num_colors, num_colors // 2)
    #weights = gaussian_weights(num_colors, num_colors // 2, num_colors / 4)

    
    colors = []
    for i in range(num_colors):
        color = [int(start_rgb[j] + weights[i] * (end_rgb[j] - start_rgb[j])) for j in range(3)]
        colors.append(rgb_to_hex(color))
    

    return colors



# Generate the color gradient
labels = ["one", "two", "three", "four", "five"]
holderDict = {}
num_colors = [19, 40, 70, 110, 150, 190]
space = [ 2, 4, 6, 8, 10]
master_colors = generate_color_gradient('#818589', '#1CE815', 19)

for i in range(len(space)):
  color_array = []
  for j in range(len(master_colors) - 1):
    color_array.extend(generate_color_gradient(master_colors[j], master_colors[j+1], space[i]))
    print(len(color_array))
  holderDict[labels[i]] = color_array

print(holderDict)
'''
num_colors = 19
colors = generate_color_gradient('#818589', '#1CE815', num_colors)

# Visualize the color swatches
plt.figure(figsize=(8, 2))

for i, color in enumerate(colors):
  plt.subplot(1, num_colors, i+1)
  plt.axis('off')
  plt.gca().set_aspect('equal')  # Ensure square shape for color patches
  plt.text(0.5, 0.5, color, ha='center', va='center', color=color, fontsize=5)

  # Adjust rectangle position to top
  rect = plt.Rectangle((0.25, 0.75), 0.5, 0.25, color=color)
  plt.gca().add_patch(rect)

# Adjust subplot spacing
plt.subplots_adjust(wspace=0.2)
plt.savefig('color_gradient.png')
print(colors)
'''