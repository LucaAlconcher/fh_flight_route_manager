import React, { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Circle, Tooltip, Polyline, useMap, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Logic for initial "Fit All" view
const BoundsHandler = ({ annotations }) => {
  const map = useMap();
  const hasInitialized = useRef(false);

  useEffect(() => {
    // Only run if we have data AND we haven't fitted the bounds yet
    if (annotations.length > 0 && !hasInitialized.current) {
      const bounds = L.latLngBounds(annotations.map(a => [a.latitude, a.longitude]));
      map.fitBounds(bounds, { padding: [50, 50] });

      // Mark as done so it never runs again during this session
      hasInitialized.current = true;
    }
  }, [annotations, map]);

  return null;
};

// Logic for "Jump to Item" when clicked in sidebar
const MapController = ({ annotations, focusedAnnoId }) => {
  const map = useMap();
  useEffect(() => {
    if (focusedAnnoId) {
      const target = annotations.find(a => a.id === focusedAnnoId);
      if (target) {
        map.setView([target.latitude, target.longitude], map.zoom, { animate: true });
      }
    }
  }, [focusedAnnoId, map, annotations]);
  return null;
};

const ViewportTracker = ({ setBounds, setZoom }) => {
  const map = useMapEvents({
    moveend: () => {
      setBounds(map.getBounds());
      setZoom(map.getZoom()); // 👈 Update zoom state
    },
  });

  useEffect(() => {
    setBounds(map.getBounds());
    setZoom(map.getZoom());
  }, [map, setBounds, setZoom]);

  return null;
};

const MapDisplay = ({ routes, annotations, validatedFlightRoutes, focusedAnnoId, setFocusedAnnoId }) => {
  const defaultCenter = [-38.95, -68.06];
  const [bounds, setBounds] = useState(null);
  const [currentZoom, setCurrentZoom] = useState(13);

  const compromisedAnnos = annotations.filter(a => a.compromised);

  const visibleAnnos = annotations
    .filter(a => {
      if (!bounds) return false;
      return bounds.contains([a.latitude, a.longitude]);
    })
    .slice(0, 500);

  return (
    <div style={{ height: '100%', width: '100%', overflow: 'hidden' }}>
      <MapContainer
        center={defaultCenter}
        zoom={currentZoom}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false} // Cleaner look
      >
        <TileLayer
          attribution='&copy; OpenStreetMap'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <BoundsHandler annotations={compromisedAnnos} />
        <MapController annotations={compromisedAnnos} focusedAnnoId={focusedAnnoId} />
        <ViewportTracker setBounds={setBounds} setZoom={setCurrentZoom}/>

        {routes.map(route => {
          if (!route.waypoints || route.waypoints.length === 0) return null;

          const originalPositions = route.waypoints.map(wp => [wp.latitude, wp.longitude]);

          const safeValidationList = Array.isArray(validatedFlightRoutes) ? validatedFlightRoutes : [];
          const validationResult = safeValidationList.find(v => v.flight_route_id === route.id);

          const isCompromised = validationResult?.compromised;
          const safeWaypoints = validationResult?.safe_waypoints || [];

          // 1. Draw original line (Green if safe, Red if compromised)
          const originalColor = isCompromised ? '#dc3545' : '#28a745';

          return (
            <React.Fragment key={route.id}>
              {/* The original full route */}
              <Polyline
                positions={originalPositions}
                pathOptions={{ color: originalColor, weight: 4, opacity: 1 }}
              >
                <Tooltip sticky className="custom-label">
                  ✈️ {route.name}
                </Tooltip>
              </Polyline>

              {/* 2. OVERLAY: The safe "cut" route (Dashed Yellow/Orange to show the new path) */}
              {isCompromised && safeWaypoints.length > 0 && (
                <Polyline
                  positions={safeWaypoints.map(wp => [wp.latitude, wp.longitude])}
                  pathOptions={{
                    color: '#ffc107', // Warning yellow/orange
                    weight: 3,
                    dashArray: '10, 10',
                    opacity: 1
                  }}
                />
              )}
            </React.Fragment>
          );
        })}

        {visibleAnnos.map(anno => (
          <Circle
            key={anno.id}
            center={[anno.latitude, anno.longitude]}
            radius={anno.compromised ? 100 : 15}
            pathOptions={{
              color: anno.color || 'red',
              fillColor: anno.color || 'red',
              fillOpacity: focusedAnnoId === anno.id ? 0.5 : 0.2,
              weight: focusedAnnoId === anno.id ? 3 : 1
            }}
            eventHandlers={{
              click: () => setFocusedAnnoId(anno.id),
              // mouseout: () => setFocusedAnnoId(null)
            }}
          >
            {(anno.compromised || currentZoom > 14) &&  (
              <Tooltip
                permanent
                direction="top"
                offset={[0, -5]}
                className="custom-label"
              >
                {anno.name}
              </Tooltip>
            )}
          </Circle>
        ))}
      </MapContainer>
    </div>
  );
};

export default MapDisplay;