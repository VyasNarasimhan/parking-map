'use client'; // This directive is crucial for components using hooks/browser APIs

import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Polygon, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';

// --- Configuration ---
const FLASK_API_URL = "http://127.0.0.1:5000";
const MAP_CENTER: L.LatLngExpression = [38.0336, -78.5080];
const INITIAL_ZOOM = 17;
const ZOOM_THRESHOLD = 18;

// --- Helper Component to manage zoom-based rendering ---
const ParkingLayers = ({ lots }: { lots: any[] }) => {
  const map = useMapEvents({
    zoomend: () => setZoom(map.getZoom()),
  });
  const [zoom, setZoom] = useState(map.getZoom());

  return zoom < ZOOM_THRESHOLD ? <SummaryView lots={lots} /> : <DetailedView lots={lots} />;
};

// --- Component for the "Zoomed Out" Summary View ---
const SummaryView = ({ lots }: { lots: any[] }) => {
  return (
    <>
      {lots.map((lot, lotIndex) => {
        const total_spaces = lot.spaces.length;
        if (total_spaces === 0) return null;

        const occupied_spaces = lot.spaces.filter((s: any) => s.occupied).length;
        const available_spaces = total_spaces - occupied_spaces;
        const occupancy_rate = occupied_spaces / total_spaces;
        const percentage_open = (available_spaces / total_spaces) * 100;

        let summary_color = 'green';
        if (occupancy_rate > 0.8) summary_color = 'red';
        else if (occupancy_rate > 0.5) summary_color = 'orange';

        const center_point: L.LatLngExpression = lot.coords.reduce(
          (avg: number[], latlng: number[]) => [avg[0] + latlng[0] / lot.coords.length, avg[1] + latlng[1] / lot.coords.length], [0, 0]
        );

        const labelIcon = L.divIcon({
          className: 'lot-label',
          html: `<b>${lot.name}</b><br>${percentage_open.toFixed(0)}% Open`,
          iconSize: [150, 36],
          iconAnchor: [75, 18]
        });

        return (
          <React.Fragment key={lotIndex}>
            <Polygon
              positions={lot.coords}
              pathOptions={{ color: summary_color, fillColor: summary_color, fillOpacity: 0.6 }}
              eventHandlers={{ click: () => alert(`${lot.name}: ${available_spaces}/${total_spaces} available`) }}
            />
            <Marker position={center_point} icon={labelIcon} />
          </React.Fragment>
        );
      })}
    </>
  );
};

// --- Component for the "Zoomed In" Detailed View ---
const DetailedView = ({ lots }: { lots: any[] }) => {
  return (
    <>
      {lots.map(lot => (
        lot.spaces.map((space: any) => (
          <Polygon
            key={space.id}
            positions={space.coords}
            pathOptions={{ color: space.occupied ? 'red' : 'green', weight: 1, fillOpacity: 0.5 }}
            eventHandlers={{ click: () => alert(`${lot.name} - Space ${space.id} (${space.occupied ? 'Occupied' : 'Available'})`) }}
          />
        ))
      ))}
    </>
  );
};

// --- The Main Map Component ---
export default function ParkingMap() {
  const [lots, setLots] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${FLASK_API_URL}/data`);
        const data = await response.json();
        setLots(data);
      } catch (error) {
        console.error("Error fetching parking data:", error);
      }
    };

    fetchData(); // Initial fetch
    const interval = setInterval(fetchData, 5000); // Poll every 5 seconds
    return () => clearInterval(interval); // Cleanup on unmount
  }, []);

  return (
    <MapContainer
      center={MAP_CENTER}
      zoom={INITIAL_ZOOM}
      maxZoom={22}
      className="map-container"
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        maxZoom={19}
        noWrap={true}
        bounds={[[ -90, -180 ], [ 90, 180 ]]}
      />
      <ParkingLayers lots={lots} />
    </MapContainer>
  );
}