'use client'; // This is now the Client Component boundary

import { useMemo } from 'react';
import dynamic from 'next/dynamic';

export default function MapLoader() {
  // The dynamic import logic is moved here, inside a Client Component
  const Map = useMemo(() => dynamic(
    () => import('@/components/ParkingMap'),
    { 
      loading: () => <p style={{textAlign: 'center', paddingTop: '20px'}}>A map is loading...</p>,
      ssr: false // This is allowed in a Client Component
    }
  ), []);

  return <Map />;
}