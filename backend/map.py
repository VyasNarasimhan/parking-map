from flask import Flask, render_template_string
import folium
import json
import random
import numpy as np

from generate_coordinates import *

app = Flask(__name__)

# Define a zoom threshold. Levels above this show details.
ZOOM_THRESHOLD = 18

@app.route("/")
def index():
    # Create the map
    m = folium.Map(location=[38.0336, -78.5080], zoom_start=17, max_zoom=22)

    with open('lots.json', 'r') as f:
        lots = json.load(f)

    # Create FeatureGroups for different zoom levels
    detailed_group = folium.FeatureGroup(name="Detailed Spaces", show=False)
    summary_group = folium.FeatureGroup(name="Lot Summary", show=True)


    for lot in lots:
        # --- Part 1: Calculate Lot Summary ---
        total_spaces = len(lot["spaces"])
        occupied_spaces = sum(1 for s in lot["spaces"] if s["occupied"])
        available_spaces = total_spaces - occupied_spaces
        occupancy_rate = occupied_spaces / total_spaces if total_spaces > 0 else 0
        
        # NEW: Calculate percentage open
        percentage_open = (available_spaces / total_spaces) * 100 if total_spaces > 0 else 0

        # Determine summary color based on occupancy
        if occupancy_rate > 0.8:
            summary_color = "red"
        elif occupancy_rate > 0.5:
            summary_color = "orange"
        else:
            summary_color = "green"

        # --- Part 2: Create the Summary Polygon ---
        folium.Polygon(
            locations=lot["coords"],
            color=summary_color,
            fill=True,
            fill_color=summary_color,
            fill_opacity=0.6,
            popup=f"<b>{lot['name']}</b><br>"
                  f"{available_spaces} / {total_spaces} Available"
        ).add_to(summary_group)
        
        # --- NEW: Part 3: Create a permanent text label for the summary view ---
        
        # 1. Calculate the center of the lot for the label's position
        lot_coords_np = np.array(lot["coords"])
        center_point = lot_coords_np.mean(axis=0).tolist()

        # 2. Create custom HTML for the label using DivIcon
        label_html = f"""
        <div style="
            background-color: rgba(255, 255, 255, 0.8);
            border: 1px solid black;
            border-radius: 5px;
            padding: 5px 8px;
            font-size: 14px;
            font-family: sans-serif;
            font-weight: bold;
            text-align: center;
            white-space: nowrap;
            ">
            {lot['name']}<br>
            {percentage_open:.0f}% Open
        </div>
        """
        
        # 3. Create the marker with the custom HTML icon
        folium.Marker(
            location=center_point,
            icon=folium.DivIcon(
                html=label_html,
                icon_size=(150, 36), # Adjust size as needed
                icon_anchor=(75, 18)   # Center the anchor
            )
        ).add_to(summary_group)


        # --- Part 4: Create the Detailed Polygons ---
        for space in lot["spaces"]:
            folium.Polygon(
                locations=space["coords"],
                color="red" if space["occupied"] else "green",
                fill=True,
                fill_opacity=0.6,
                popup=f"{lot['name']} – Space {space['id']} "
                      f"({'Occupied' if space['occupied'] else 'Available'})",
            ).add_to(detailed_group)

    # Add the feature groups to the map
    detailed_group.add_to(m)
    summary_group.add_to(m)

    # The original JavaScript for toggling layers doesn't need any changes!
    map_name = m.get_name()
    detailed_layer_name = detailed_group.get_name()
    summary_layer_name = summary_group.get_name()

    js = f"""
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const map = {map_name};
            const detailedLayer = {detailed_layer_name};
            const summaryLayer = {summary_layer_name};
            const zoomThreshold = {ZOOM_THRESHOLD};

            function toggleLayers() {{
                const currentZoom = map.getZoom();
                if (currentZoom >= zoomThreshold) {{
                    if (!map.hasLayer(detailedLayer)) {{ map.addLayer(detailedLayer); }}
                    if (map.hasLayer(summaryLayer)) {{ map.removeLayer(summaryLayer); }}
                }} else {{
                    if (map.hasLayer(detailedLayer)) {{ map.removeLayer(detailedLayer); }}
                    if (!map.hasLayer(summaryLayer)) {{ map.addLayer(summaryLayer); }}
                }}
            }}
            toggleLayers();
            map.on('zoomend', toggleLayers);
        }});
    </script>
    """
    m.get_root().html.add_child(folium.Element(js))

    map_html = m._repr_html_()

    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Parking Map</title>
        <style>
            html, body {{ margin: 0; padding: 0; height: 100%; }}
            .leaflet-container {{ height: 100vh; }}
        </style>
    </head>
    <body>
        {map_html}
    </body>
    </html>
    """.format(map_html=map_html)

    return template

if __name__ == "__main__":
    app.run(debug=True)