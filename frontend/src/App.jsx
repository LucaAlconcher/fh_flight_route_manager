import React, { useState } from 'react';
import { DataProvider } from './context/DataProvider';
import FlightRoutes from './tabs/FlightRoutes';
import Annotations from './tabs/Annotations';
import ExecutionDashboard from './tabs/ExecutionDashboard';

const styles = {
  appWrapper: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    width: '100vw',
    fontFamily: 'sans-serif',
    overflow: 'hidden'
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    background: '#333',
    padding: '0 20px',
    height: '50px',
    color: 'white'
  },
  tabButton: (active) => ({
    height: '100%',
    padding: '0 25px',
    cursor: 'pointer',
    border: 'none',
    background: active ? '#444' : 'transparent',
    color: 'white',
    borderBottom: active ? '3px solid #007bff' : 'none',
    fontWeight: 'bold',
    transition: 'background 0.2s'
  }),
  mainContent: {
    flex: 1,
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column'
  }
};

const App = () => {
  const [activeTab, setActiveTab] = useState('flights');

  return (
    <DataProvider>
      <div style={styles.appWrapper}>
        <header style={styles.header}>
          <div style={{ marginRight: '30px', fontWeight: 'bold', fontSize: '1.2rem' }}>
            FH Manager
          </div>
          <button
            style={styles.tabButton(activeTab === 'flights')}
            onClick={() => setActiveTab('flights')}
          >
            Flight Routes
          </button>
          <button
            style={styles.tabButton(activeTab === 'annotations')}
            onClick={() => setActiveTab('annotations')}
          >
            Annotations
          </button>
          <button
            style={styles.tabButton(activeTab === 'dashboard')}
            onClick={() => setActiveTab('dashboard')}
          >
            Dashboard
          </button>
          <button
            style={styles.tabButton(activeTab === 'settings')}
            onClick={() => setActiveTab('settings')}
          >
            Settings
          </button>
        </header>

        <main style={styles.mainContent}>
          {activeTab === 'flights' && <FlightRoutes />}
          {activeTab === 'annotations' && <Annotations />}
          {activeTab === 'dashboard' && <ExecutionDashboard />}
          {activeTab === 'settings' && (
            <div style={{ padding: '40px' }}>
              <h3>Settings</h3>
              <p>Configuration options will go here.</p>
            </div>
          )}
        </main>
      </div>
    </DataProvider>
  );
};

export default App;