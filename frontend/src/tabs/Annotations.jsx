import React from 'react';
import { DragDropContext } from '@hello-pangea/dnd';
import { useData } from '../context/DataProvider';
import SearchableList from '../components/SearchableList';

const Annotations = () => {
  const { annotations, toggleAnnotationCompromised, refreshAnnotations } = useData();

  const onDragEnd = (result) => {
    const { source, destination, draggableId } = result;
    if (!destination) return;

    // If moved between lists, toggle the compromised status
    if (source.droppableId !== destination.droppableId) {
      toggleAnnotationCompromised(draggableId);
    }
  };

  const safeAnnos = annotations.filter(a => !a.compromised);
  const compromisedAnnos = annotations.filter(a => a.compromised);

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <div style={{ display: 'flex', justifyContent: 'space-around', padding: '10px', gap: '10px' }}>
        <SearchableList
          title="Annotations"
          refresh={refreshAnnotations}
          items={safeAnnos}
          dropId="safe"
        />
        <SearchableList
          title="Compromised"
          items={compromisedAnnos}
          dropId="compromised"
        />
      </div>
    </DragDropContext>
  );
};

export default Annotations;