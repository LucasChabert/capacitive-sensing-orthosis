import numpy as np
import matplotlib.pyplot as plt
import sys
import pandas as pd

def compute_stats(data):
    """
    Compute mean and standard deviation with validation.
    """
    if not isinstance(data, (list, tuple, np.ndarray)):
        raise TypeError("Data must be a list, tuple, or NumPy array of numbers.")
    if len(data) == 0:
        raise ValueError("Data list cannot be empty.")

    try:
        arr = np.array(data, dtype=float)
    except ValueError:
        raise ValueError("All items in data must be numeric.")

    mean = np.mean(arr)
    std = np.std(arr, ddof=1)  # sample standard deviation
    return arr, mean, std


def plot_normal_distribution(data):
    """
    Compute stats and plot histogram + normal distribution curve.
    """
    try:
        arr, mean, std = compute_stats(data)
    except Exception as e:
        print("Error:", e)
        sys.exit(1)

    # Generate x values for smooth curve
    x = np.linspace(arr.min() - 3*std, arr.max() + 3*std, 500)
    
    # Normal distribution formula
    y = (1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean) / std)**2)

    # Plot histogram
    plt.hist(arr, bins=20, density=True, alpha=0.6, color='skyblue', edgecolor='black')

    # Plot normal curve
    plt.plot(x, y, color='red', linewidth=2, label="Normal Distribution")

    plt.title("Normal Distribution Fit")
    plt.xlabel("Value")
    plt.ylabel("Density")
    plt.legend()
    plt.grid(True)
    plt.show()

    print(f"Mean: {mean}")
    print(f"Standard deviation: {std}")


# Example usage:
if __name__ == "__main__":
    # Example data (replace with your own)
    df = pd.read_csv("teleplot_2026-6-15_13-30.csv")
    sample_data = df["C1 (pF)"].to_numpy()

    plot_normal_distribution(sample_data)

