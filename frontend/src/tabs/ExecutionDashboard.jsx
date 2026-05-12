import React, { useEffect, useRef } from 'react';
import { useData } from '../context/DataProvider';
import MapDisplay from '../components/MapDisplay';

const ExecutionDashboard = () => {
  const { flightRoutes, annotations, syncRouteDetails, downloadRouteFiles, processRouteFiles, validateRoutes, setFocusedAnnoId, focusedAnnoId, validatedFlightRoutes } = useData();
  const listRef = useRef({}); // Stores DOM refs for auto-scrolling

  const executionRoutes = flightRoutes.filter(r => r.is_execution_route);
  const compromisedAnnos = annotations.filter(a => a.compromised);

  const hasPending = executionRoutes.some(r => r.sync_status === 'PENDING');
  const hasSynced = executionRoutes.some(r => r.sync_status === 'SYNCED');
  const hasDownloaded = executionRoutes.some(r => r.sync_status === 'DOWNLOADED');

  const allProcessed = executionRoutes.every(r => r.sync_status === 'PROCESSED');

  // Auto-scroll logic: triggers when MapDisplay updates focusedAnnoId
  useEffect(() => {
    if (focusedAnnoId && listRef.current[focusedAnnoId]) {
      listRef.current[focusedAnnoId].scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      });
    }
  }, [focusedAnnoId]);

  const columnStyle = {
    flex: '0 0 1',
    background: '#f8f9fa',
    padding: '15px',
    borderRight: '1px solid #ddd',
    overflowY: 'auto',
    height: 'calc(100vh - 50px)'
  };

  const itemStyle = (isFocused, itemColor) => ({
    padding: '10px',
    background: isFocused ? '#e7f1ff' : 'white',
    marginBottom: '8px',
    borderRadius: '4px',
    // 1. General border applies to all sides
    // border: isFocused ? '1px solid #007bff' : '1px solid #eee',
    // 2. We explicitly override the Left side AFTER the general border
    borderLeft: `6px solid ${itemColor}`,
    fontSize: '13px',
    cursor: 'pointer',
    transition: 'background 0.2s, border 0.2s'
  });

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 50px)', width: '100vw' }}>
      {/* Column 1: Execution Routes */}
      <div style={columnStyle}>
        <h4 style={{ marginTop: 0 }}>✈️ Execution Routes</h4>
        
        {executionRoutes.length === 0 ? (
          <p style={{ fontSize: '12px', color: '#888' }}>No routes selected.</p>
        ) : (
          <>
            <button
              disabled={!hasPending}
              onClick={syncRouteDetails}
              style={actionButtonStyle(hasPending, '#007bff')}
            >
              Fetch Route Details
            </button>
            <button
              disabled={!hasSynced}
              onClick={downloadRouteFiles}
              style={actionButtonStyle(hasSynced, '#007bff')}
            >
              Download & Extract KMZ
            </button>
            <button
              disabled={!hasDownloaded}
              onClick={processRouteFiles}
              style={actionButtonStyle(hasDownloaded, '#007bff')}
            >
              Process Routes
            </button>
            <button
              disabled={!allProcessed}
              onClick={validateRoutes}
              style={actionButtonStyle(allProcessed, '#007bff')}
            >
              Validate
            </button>
          </>
        )}

        {executionRoutes.map(r => (
          <div key={r.id} style={{ ...itemStyle(false), cursor: 'default' }}>
            <strong>{r.name}</strong> <span>{r.sync_status}</span>
          </div>
        ))}

      </div>

      {/* Column 2: Compromised Annotations */}
      <div style={columnStyle}>
        <h4 style={{ marginTop: 0 }}>⚠️ Compromised</h4>
        {compromisedAnnos.map(a => (
          <div
            key={a.id}
            ref={el => listRef.current[a.id] = el}
            onClick={() => setFocusedAnnoId(a.id)}
            onClick={() => setFocusedAnnoId(a.id)}
            // onMouseLeave={() => setFocusedAnnoId(null)}
            style={itemStyle(focusedAnnoId === a.id, a.color)}
          >
            <strong>{a.name}</strong>
            {/* <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>
              {a.latitude.toFixed(4)}, {a.longitude.toFixed(4)}
            </div> */}
          </div>
        ))}
        {compromisedAnnos.length === 0 && <p style={{ fontSize: '12px', color: '#888' }}>No compromised points.</p>}
      </div>

      {/* Column 3: The Map */}
      <div style={{ flex: 1, position: 'relative' }}>
        <MapDisplay
          routes={executionRoutes}
          annotations={annotations}
          validatedFlightRoutes={validatedFlightRoutes}
          focusedAnnoId={focusedAnnoId}
          setFocusedAnnoId={setFocusedAnnoId}
        />
      </div>
    </div>
  );
};

const actionButtonStyle = (enabled, color) => ({
  width: '100%',
  padding: '10px',
  backgroundColor: enabled ? color : '#ccc',
  color: 'white',
  border: 'none',
  borderRadius: '4px',
  fontWeight: 'bold',
  cursor: enabled ? 'pointer' : 'not-allowed',
  fontSize: '12px',
  transition: 'all 0.2s'
});

export default ExecutionDashboard;