'use client';

import React, { useEffect, useState } from 'react';
import {
  GoogleMap,
  Marker,
  Polygon as GPolygon,
  useLoadScript
} from '@react-google-maps/api';

type LatLngTuple = [number, number];
type LatLngLiteral = google.maps.LatLngLiteral;

// --- Configuration ---
const GOOGLE_MAPS_API_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
const FLASK_API_URL = "http://127.0.0.1:5000";
const MAP_CENTER: LatLngLiteral = { lat: 38.0336, lng: -78.5080 };
const INITIAL_ZOOM = 17;
const ZOOM_THRESHOLD = 18;
const MAP_CONTAINER_STYLE = { width: '100%', height: '100vh' };

const availabilityColor = (percentageOpen: number) => {
  if (percentageOpen >= 50) return '#2ecc71'; // green-ish
  if (percentageOpen >= 25) return '#f1c40f'; // yellow
  return '#e74c3c'; // red
};

const toLatLngLiteral = (coords: LatLngTuple[]): LatLngLiteral[] =>
  coords.map(([lat, lng]) => ({ lat, lng }));

// --- Helper Component to manage zoom-based rendering ---
const ParkingLayers = ({ lots, zoom }: { lots: any[]; zoom: number }) => {
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
        const percentageColor = availabilityColor(percentage_open);

        let summary_color = 'green';
        if (occupancy_rate > 0.8) summary_color = 'red';
        else if (occupancy_rate > 0.5) summary_color = 'orange';

        const path = toLatLngLiteral(lot.coords);
        const center_point: LatLngLiteral = path.reduce(
          (avg, point) => ({
            lat: avg.lat + point.lat / path.length,
            lng: avg.lng + point.lng / path.length
          }),
          { lat: 0, lng: 0 }
        );

        // Create custom icon for the badge
        const badgeIcon: google.maps.Icon = {
          url: `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`
            <svg width="150" height="48" xmlns="http://www.w3.org/2000/svg">
              <foreignObject width="150" height="48">
                <div xmlns="http://www.w3.org/1999/xhtml" style="
                  text-align: center;
                  font-size: 12px;
                  font-weight: 600;
                  color: #fff;
                  background: ${percentageColor};
                  padding: 12px;
                  border-radius: 8px;
                  box-shadow: 0 2px 6px rgba(0,0,0,0.25);
                  font-family: sans-serif;
                ">
                  <div>${lot.name}</div>
                  <div style="margin-top: 2px;">${percentage_open.toFixed(0)}% Open</div>
                </div>
              </foreignObject>
            </svg>
          `)}`,
          scaledSize: new google.maps.Size(150, 48),
          anchor: new google.maps.Point(75, 24),
        };

        return (
          <React.Fragment key={lotIndex}>
            <GPolygon
              path={path}
              options={{
                strokeColor: summary_color,
                strokeWeight: 2,
                fillColor: summary_color,
                fillOpacity: 0.45
              }}
              onClick={() => alert(`${lot.name}: ${available_spaces}/${total_spaces} available`)}
            />
            <Marker
              position={center_point}
              icon={badgeIcon}
              clickable={false}
            />
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
      {lots.map((lot) =>
        lot.spaces.map((space: any) => (
          <GPolygon
            key={space.id}
            path={toLatLngLiteral(space.coords)}
            options={{
              strokeColor: space.occupied ? '#8b0000' : '#006400', // darker border
              fillColor: space.occupied ? '#e74c3c' : '#2ecc71',
              strokeWeight: 1.5,
              fillOpacity: 0.9
            }}
            onClick={() =>
              alert(`${lot.name} - Space ${space.id} (${space.occupied ? 'Occupied' : 'Available'})`)
            }
          />
        ))
      )}
    </>
  );
};

// --- The Main Map Component ---
export default function ParkingMap() {
  const [lots, setLots] = useState([]);
  const [zoom, setZoom] = useState(INITIAL_ZOOM);
  const [map, setMap] = useState<google.maps.Map | null>(null);

  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: GOOGLE_MAPS_API_KEY ?? ''
  });

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

  useEffect(() => {
    if (map) {
      setZoom(map.getZoom() ?? INITIAL_ZOOM);
    }
  }, [map]);

  if (!GOOGLE_MAPS_API_KEY) {
    return <p style={{ textAlign: 'center', paddingTop: '20px' }}>Missing Google Maps API key.</p>;
  }

  if (loadError) {
    return <p style={{ textAlign: 'center', paddingTop: '20px' }}>Failed to load Google Maps.</p>;
  }

  if (!isLoaded) {
    return <p style={{ textAlign: 'center', paddingTop: '20px' }}>Loading map...</p>;
  }

  return (
    <GoogleMap
      mapContainerStyle={MAP_CONTAINER_STYLE}
      center={MAP_CENTER}
      zoom={INITIAL_ZOOM}
      options={{
        mapTypeId: 'satellite',
        streetViewControl: false,
        fullscreenControl: false,
        mapTypeControl: false,
        zoomControl: true
      }}
      onLoad={(mapInstance) => setMap(mapInstance)}
      onZoomChanged={() => map && setZoom(map.getZoom() ?? INITIAL_ZOOM)}
    >
      <ParkingLayers lots={lots} zoom={zoom} />
    </GoogleMap>
  );
}