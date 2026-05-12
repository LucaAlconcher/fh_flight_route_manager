import React, { useState } from 'react';
import { Droppable, Draggable } from '@hello-pangea/dnd';
import { Search, SpaceIcon } from 'lucide-react';

const SearchableList = ({ title, refresh, items, dropId }) => {
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(100);

  const filtered = items.filter(i =>
    i.name.toLowerCase().includes(query.toLowerCase())
  );

  const visibleItems = filtered.slice(0, limit);

  return (
    <div style={{
      width: '30%',
      background: '#f4f4f4',
      borderRadius: '8px',
      display: 'flex',
      flexDirection: 'column',
      height: 'calc(100vh - 100px)', // Take up remaining screen height
      border: '1px solid #ddd'
    }}>
      {/* Fixed Header Section */}
      <div style={{ padding: '15px 15px 5px 15px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <h3 style={{ margin: 0 }}>{title} ({filtered.length})</h3>
          {refresh && (
            <button
              onClick={refresh}
              style={{
                padding: '4px 10px',
                fontSize: '12px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              🔄 Refresh
            </button>
          )}
        </div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          background: 'white',
          padding: '8px 12px',
          borderRadius: '4px',
          border: '1px solid #ccc'
        }}>
          <Search size={16} color="#666" />
          <input
            style={{ border: 'none', marginLeft: '8px', outline: 'none', width: '100%', fontSize: '14px' }}
            placeholder="Filter by name..."
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Scrollable List Area */}
      <Droppable droppableId={dropId}>
        {(provided) => (
          <div
            {...provided.droppableProps}
            ref={provided.innerRef}
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '10px 15px'
            }}
          >
            {visibleItems.map((item, index) => (
              <Draggable key={item.id} draggableId={item.id} index={index}>
                {(provided) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.draggableProps}
                    {...provided.dragHandleProps}
                    style={{
                      padding: '12px',
                      margin: '0 0 8px 0',
                      background: 'white',
                      borderRadius: '4px',
                      border: '1px solid #ddd',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                      ...provided.draggableProps.style
                    }}
                  >
                    <div style={{ fontWeight: '500', color: '#333' }}>{item.name}</div>
                  </div>
                )}
              </Draggable>
            ))}
            {provided.placeholder}
          </div>
        )}
      </Droppable>
    </div>
  );
};

export default SearchableList;