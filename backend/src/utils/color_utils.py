import numpy as np
from scipy.stats import norm
from typing import List, Dict

def modified_sigmoid(x: np.ndarray, k: float = 0.005) -> np.ndarray:
    """Modified sigmoid function with adjustable steepness."""
    return 1 / (1 + np.exp(-k * x))

def sigmoid(x: np.ndarray) -> np.ndarray:
    """Standard sigmoid function."""
    return 1 / (1 + np.exp(-x))

def tanh(x: np.ndarray) -> np.ndarray:
    """Hyperbolic tangent function."""
    return (np.exp(x) - np.exp(-x)) / (np.exp(x) + np.exp(-x))

def triangular_weights(num_colors: int, peak_index: int) -> np.ndarray:
    """Generate triangular weight distribution."""
    x = np.arange(num_colors)
    weights = np.minimum(x, num_colors - x - 1)
    weights = weights / np.max(weights)
    return weights

def gaussian_weights(num_colors: int, mean: float, std: float) -> np.ndarray:
    """Generate Gaussian weight distribution."""
    x = np.linspace(0, num_colors - 1, num_colors)
    weights = norm.pdf(x, loc=mean, scale=std)
    cumulative_weights = np.cumsum(weights)
    cumulative_weights /= cumulative_weights[-1]
    return cumulative_weights

def custom_weights(num_colors: int, peak_width: float) -> np.ndarray:
    """Generate custom weight distribution with adjustable peak width."""
    x = np.arange(num_colors)
    weights = np.abs(x - (num_colors - 1) / 2)
    weights = 1 - weights / max(weights)
    weights = weights ** peak_width
    return weights

def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb: tuple) -> str:
    """Convert RGB tuple to hex color string."""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

def generate_color_gradient(start_hex: str, end_hex: str, num_colors: int) -> List[str]:
    """
    Generate color gradient between two hex colors.
    
    Args:
        start_hex: Starting color in hex format
        end_hex: Ending color in hex format
        num_colors: Number of colors in gradient
        
    Returns:
        List of hex color strings
    """
    start_rgb = hex_to_rgb(start_hex)
    end_rgb = hex_to_rgb(end_hex)

    # Generate sigmoid weights
    x = np.linspace(-6, 6, num_colors)
    weights = sigmoid(x)
    
    colors = []
    for i in range(num_colors):
        color = [int(start_rgb[j] + weights[i] * (end_rgb[j] - start_rgb[j])) for j in range(3)]
        colors.append(rgb_to_hex(color))
    
    return colors

def generate_color_mapping() -> Dict[str, List[str]]:
    """
    Generate predefined color mappings for different intensity levels.
    
    Returns:
        Dictionary mapping intensity labels to color arrays
    """
    labels = ["one", "two", "three", "four", "five"]
    holder_dict = {}
    space = [2, 4, 6, 8, 10]
    master_colors = generate_color_gradient('#818589', '#1CE815', 19)
    
    for i in range(len(space)):
        color_array = []
        for j in range(len(master_colors) - 1):
            color_array.extend(
                generate_color_gradient(master_colors[j], master_colors[j+1], space[i])
            )
        holder_dict[labels[i]] = color_array
    
    return holder_dict