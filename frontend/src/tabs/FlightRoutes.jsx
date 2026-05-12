import React from 'react';
import { DragDropContext } from '@hello-pangea/dnd';
import { useData } from '../context/DataProvider';
import SearchableList from '../components/SearchableList';

const FlightRoutes = () => {
  const { flightRoutes, toggleFlightRouteExecution, refreshFlightRoutes } = useData();

  const handleDragEnd = (result) => {
    if (!result.destination) return;
    // If the item moved to a different list
    if (result.source.droppableId !== result.destination.droppableId) {
      toggleFlightRouteExecution(result.draggableId);
    }
  };

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: '20px' }}>
        <SearchableList
          title="Available"
          refresh={refreshFlightRoutes}
          items={flightRoutes.filter(r => !r.is_execution_route)}
          dropId="available"
        />
        <SearchableList
          title="Execution"
          items={flightRoutes.filter(r => r.is_execution_route)}
          dropId="execution"
        />
      </div>
    </DragDropContext>
  );
};

export default FlightRoutes;