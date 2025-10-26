import json
import numpy as np
import time
import random

from generate_coordinates import *

A = np.array([38.030907, -78.511921])
B = np.array([38.031354, -78.511280])
C = np.array([38.031283, -78.511202])
D = np.array([38.030836, -78.511848])
CARS_PER_ROW = 29

while True:

    spaces_coordinates = generate_diagonal_parking_spaces(A, B, C, D, n_row=CARS_PER_ROW)
    all_spaces_coordinates = spaces_coordinates[0] + spaces_coordinates[1]
    spaces = []
    for i, coords in enumerate(all_spaces_coordinates):
        coords = [c.tolist() for c in coords]
        spaces.append({
            "id": i,
            "coords": coords,
            "occupied": random.choice([True, False])
        })

    lots = [
        {
            "name": "Stadium Parking Lot",
            "spaces": spaces,
            "coords": [A.tolist(), B.tolist(), C.tolist(), D.tolist()]
        }
    ]

    with open("lots.json", "w", encoding="utf-8") as json_file:
        # 3. Use json.dump() to write the dictionary to the file
        # 'indent=4' makes the JSON output human-readable with 4-space indentation.
        json.dump(lots, json_file, indent=4)
    
    time.sleep(5)