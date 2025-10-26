import numpy as np

def interpolate(p1, p2, n):
    """Return n+1 evenly spaced points between p1 and p2 (inclusive)."""
    return [p1 + (p2 - p1) * i / n for i in range(n + 1)]

def generate_diagonal_parking_spaces(A, B, C, D, n_row):
    """
    Generate parking space corner coordinates for a diagonal rectangular lot
    divided into two rows (works for arbitrary orientation).

    A, B, C, D: np.array([x, y]) or [lat, lon] corners in order (clockwise)
    n_row: number of spaces in each row
    """
    # Split the left and right edges into halves to separate the two rows
    left_mid_top = A + (D - A) * 0.5
    right_mid_top = B + (C - B) * 0.5

    # Divide the top and midline for Row 1
    top_edge_points = interpolate(A, B, n_row)
    mid_top_points = interpolate(left_mid_top, right_mid_top, n_row)

    # Divide the midline and bottom for Row 2
    mid_bottom_points = interpolate(left_mid_top, right_mid_top, n_row)
    bottom_edge_points = interpolate(D, C, n_row)

    # Row 1: between top and midline
    row1_spaces = []
    for i in range(n_row):
        space = [
            top_edge_points[i],
            top_edge_points[i+1],
            mid_top_points[i+1],
            mid_top_points[i]
        ]
        row1_spaces.append(space)

    # Row 2: between midline and bottom
    row2_spaces = []
    for i in range(n_row):
        space = [
            mid_bottom_points[i],
            mid_bottom_points[i+1],
            bottom_edge_points[i+1],
            bottom_edge_points[i]
        ]
        row2_spaces.append(space)

    return row1_spaces, row2_spaces

if __name__ == '__main__':
    # Example usage (diagonal lot)
    A = np.array([38.030907, -78.511922])
    B = np.array([38.031349, -78.511274])
    C = np.array([38.031286, -78.511200])
    D = np.array([38.030842, -78.511844])

    row1, row2 = generate_diagonal_parking_spaces(A, B, C, D, n_row1=5, n_row2=5)

    for i, space in enumerate(row1 + row2, start=1):
        print(f"Space {i}: {np.round(space, 6)}")
