import React, { createContext, useContext, useState, useEffect } from 'react';

const DataContext = createContext();

export const DataProvider = ({ children }) => {
  const [flightRoutes, setFlightRoutes] = useState([]);
  const [annotations, setAnnotations] = useState([]);

  const [validatedFlightRoutes, setValidatedFlightRoutes] = useState([]);

  const [focusedAnnoId, setFocusedAnnoId] = useState(null);

  // Fetch from our Python Backend
  const getFlightRoutes = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/flight_routes', {
        method: 'GET'
      });
      const data = await response.json();
      setFlightRoutes(data);
    } catch (err) {
      console.error("Sync failed", err);
    }
  };

  const refreshFlightRoutes = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/flight_routes/sync', {
        method: 'POST'
      });
      const data = await response.json();
      setFlightRoutes(data);
    } catch (err) {
      console.error("Sync failed", err);
    }
  };

  const getAnnotations = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/annotations');
      const data = await response.json();
      setAnnotations(data);
    } catch (err) {
      console.error("Annotations fetch failed", err);
    }
  };

  const refreshAnnotations = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/annotations/sync', { method: 'POST' });
      const data = await response.json();
      await getAnnotations()
    } catch (err) {
      console.error("Annotations fetch failed", err);
    }
  };

  const syncRouteDetails = async () => {
    try {
      await fetch('http://localhost:8000/api/flight_routes/details', { method: 'POST' });
      await getFlightRoutes(); // Refresh the list so the UI shows the new data
    } catch (err) {
      console.error("Sync failed", err);
    }
  };

  const downloadRouteFiles = async () => {
    try {
      await fetch('http://localhost:8000/api/flight_routes/download_files', { method: 'POST' });
      await getFlightRoutes(); // Refresh the list so the UI shows the new data
    } catch (err) {
      console.error("Sync failed", err);
    }
  };

  const processRouteFiles = async () => {
    try {
      await fetch('http://localhost:8000/api/flight_routes/process_files', { method: 'POST' });
      await getFlightRoutes(); // Refresh the list so the UI shows the new data
    } catch (err) {
      console.error("Sync failed", err);
    }
  };

  const validateRoutes = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/flight_routes/validate', { method: 'POST' });
      const data = await response.json();
      setValidatedFlightRoutes(data.route_collisions)
    } catch (err) {
      console.error("Sync failed", err);
    }

  }

  const toggleFlightRouteExecution = async (id) => {
    // 1. Optimistic Update: Change UI immediately for smoothness
    setFlightRoutes(prev => prev.map(r =>
      r.id === id ? { ...r, is_execution_route: !r.is_execution_route } : r
    ));

    try {
      // 2. Persist to Backend
      const response = await fetch(`http://localhost:8000/api/flight_routes/toggle_execution/${id}`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error("Failed to persist change");
      }
    } catch (err) {
      console.error("Persistence failed, rolling back UI", err);
      // 3. Rollback: If the API fails, flip it back
      setFlightRoutes(prev => prev.map(r =>
        r.id === id ? { ...r, is_execution_route: !r.is_execution_route } : r
      ));
    }
  };

  const toggleAnnotationCompromised = async (id) => {
    // Optimistic update
    setAnnotations(prev => prev.map(a =>
      a.id === id ? { ...a, compromised: !a.compromised } : a
    ));

    try {
      await fetch(`http://localhost:8000/api/annotations/toggle_compromised/${id}`, {
        method: 'POST'
      });
    } catch (err) {
      // Rollback
      setAnnotations(prev => prev.map(a =>
        a.id === id ? { ...a, compromised: !a.compromised } : a
      ));
    }
  };

  useEffect(() => {
    getFlightRoutes();
    getAnnotations();
  }, []);

  return (
    <DataContext.Provider value={{
      flightRoutes, getFlightRoutes, refreshFlightRoutes, toggleFlightRouteExecution, syncRouteDetails, downloadRouteFiles, processRouteFiles,
      annotations, getAnnotations, refreshAnnotations, toggleAnnotationCompromised,
      focusedAnnoId, setFocusedAnnoId,
      validatedFlightRoutes, validateRoutes,

    }}>
      {children}
    </DataContext.Provider>
  );
};

export const useData = () => useContext(DataContext);