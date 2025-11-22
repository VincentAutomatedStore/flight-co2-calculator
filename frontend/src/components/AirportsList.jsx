import React, { useState, useEffect } from 'react';

function AirportsList() {
  const [airports, setAirports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(50);

  useEffect(() => {
    fetchAirports();
  }, []);

    const fetchAirports = async () => {
    try {
        setLoading(true);
        const response = await fetch('/api/v2/automation/airports-list');
        if (response.ok) {
        const data = await response.json();
        if (data.success) {
            setAirports(data.airports);
        } else {
            throw new Error(data.error || 'Failed to fetch airports');
        }
        } else {
        throw new Error('Failed to fetch airports');
        }
    } catch (err) {
        setError('Failed to load airports data');
        console.error('Error fetching airports:', err);
    } finally {
        setLoading(false);
    }
    };

  const filteredAirports = airports.filter(airport =>
    airport.iata_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    airport.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    airport.city?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    airport.country?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Pagination
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentAirports = filteredAirports.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredAirports.length / itemsPerPage);

  const styles = {
    container: {
      background: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(10px)',
      borderRadius: '25px',
      padding: '40px',
      boxShadow: '0 25px 50px rgba(0, 0, 0, 0.15)',
      border: '1px solid rgba(255, 255, 255, 0.3)',
      minHeight: '600px'
    },
    header: {
      textAlign: 'center',
      marginBottom: '30px'
    },
    title: {
      fontSize: '2.5rem',
      fontWeight: 'bold',
      background: 'linear-gradient(135deg, #1e40af 0%, #047857 100%)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      marginBottom: '10px'
    },
    subtitle: {
      fontSize: '1.1rem',
      color: '#6b7280',
      marginBottom: '20px'
    },
    stats: {
      display: 'flex',
      justifyContent: 'center',
      gap: '20px',
      marginBottom: '30px',
      flexWrap: 'wrap'
    },
    statCard: {
      background: 'linear-gradient(135deg, #3b82f6 0%, #10b981 100%)',
      color: 'white',
      padding: '20px',
      borderRadius: '15px',
      textAlign: 'center',
      minWidth: '150px',
      boxShadow: '0 10px 25px rgba(59, 130, 246, 0.3)'
    },
    statValue: {
      fontSize: '2rem',
      fontWeight: 'bold',
      marginBottom: '5px'
    },
    statLabel: {
      fontSize: '0.9rem',
      opacity: 0.9
    },
    searchContainer: {
      marginBottom: '30px',
      position: 'relative'
    },
    searchInput: {
      width: '100%',
      padding: '15px 20px 15px 50px',
      border: '2px solid #e5e7eb',
      borderRadius: '15px',
      fontSize: '1.1rem',
      transition: 'all 0.3s ease',
      boxSizing: 'border-box'
    },
    searchIcon: {
      position: 'absolute',
      left: '20px',
      top: '50%',
      transform: 'translateY(-50%)',
      fontSize: '1.2rem',
      color: '#6b7280'
    },
    tableContainer: {
      background: 'white',
      borderRadius: '15px',
      overflow: 'hidden',
      boxShadow: '0 5px 15px rgba(0, 0, 0, 0.1)',
      marginBottom: '30px'
    },
    table: {
      width: '100%',
      borderCollapse: 'collapse'
    },
    tableHeader: {
      background: 'linear-gradient(135deg, #3b82f6 0%, #10b981 100%)',
      color: 'white'
    },
    tableHeaderCell: {
      padding: '15px 20px',
      textAlign: 'left',
      fontWeight: '600',
      fontSize: '1rem'
    },
    tableRow: {
      borderBottom: '1px solid #f3f4f6',
      transition: 'background 0.2s ease'
    },
    tableRowHover: {
      background: '#f8fafc'
    },
    tableCell: {
      padding: '15px 20px',
      fontSize: '0.95rem',
      color: '#374151'
    },
    iataCode: {
      background: '#3b82f6',
      color: 'white',
      padding: '4px 8px',
      borderRadius: '6px',
      fontWeight: 'bold',
      fontSize: '0.8rem'
    },
    pagination: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      gap: '15px',
      marginTop: '20px'
    },
    pageButton: {
      padding: '10px 20px',
      border: '2px solid #e5e7eb',
      background: 'white',
      borderRadius: '10px',
      cursor: 'pointer',
      fontSize: '1rem',
      fontWeight: '600',
      transition: 'all 0.3s ease'
    },
    pageButtonActive: {
      background: 'linear-gradient(135deg, #3b82f6 0%, #10b981 100%)',
      color: 'white',
      borderColor: 'transparent'
    },
    pageInfo: {
      color: '#6b7280',
      fontSize: '1rem'
    },
    loading: {
      textAlign: 'center',
      padding: '60px',
      color: '#6b7280',
      fontSize: '1.1rem'
    },
    error: {
      background: '#fef2f2',
      border: '1px solid #fecaca',
      color: '#dc2626',
      padding: '20px',
      borderRadius: '15px',
      textAlign: 'center',
      margin: '20px 0'
    },
    emptyState: {
      textAlign: 'center',
      padding: '60px',
      color: '#6b7280'
    },
    emptyIcon: {
      fontSize: '4rem',
      marginBottom: '20px'
    }
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>
          <div style={{ fontSize: '3rem', marginBottom: '20px' }}>⏳</div>
          Loading airports database...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.error}>
          <div style={{ fontSize: '2rem', marginBottom: '10px' }}>⚠️</div>
          {error}
          <button 
            onClick={fetchAirports}
            style={{
              marginTop: '15px',
              padding: '10px 20px',
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer'
            }}
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h2 style={styles.title}>Airports Database</h2>
        <p style={styles.subtitle}>
          Complete list of airports available for flight calculations
        </p>
      </div>

      {/* Statistics */}
      <div style={styles.stats}>
        <div style={styles.statCard}>
          <div style={styles.statValue}>{airports.length}</div>
          <div style={styles.statLabel}>Airports Loaded</div>
        </div>
        <div style={{...styles.statCard, background: 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)'}}>
          <div style={styles.statValue}>{filteredAirports.length}</div>
          <div style={styles.statLabel}>Filtered Results</div>
        </div>
        <div style={{...styles.statCard, background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'}}>
          <div style={styles.statValue}>{currentPage}</div>
          <div style={styles.statLabel}>Current Page</div>
        </div>
      </div>

      {/* Search */}
      <div style={styles.searchContainer}>
        <span style={styles.searchIcon}>🔍</span>
        <input
          type="text"
          placeholder="Search airports by code, name, city, or country..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setCurrentPage(1); // Reset to first page when searching
          }}
          style={styles.searchInput}
        />
      </div>

        {/* Airports Table */}
        {currentAirports.length > 0 ? (
        <>
            <div style={styles.tableContainer}>
            <table style={styles.table}>
                <thead style={styles.tableHeader}>
                <tr>
                    <th style={styles.tableHeaderCell}>IATA Code</th>
                    <th style={styles.tableHeaderCell}>Airport Name</th>
                    <th style={styles.tableHeaderCell}>City</th>
                    <th style={styles.tableHeaderCell}>Country</th>
                    <th style={styles.tableHeaderCell}>Coordinates</th>
                </tr>
                </thead>
                <tbody>
                {currentAirports.map((airport, index) => (
                    <tr 
                    key={airport.iata_code || index}
                    style={styles.tableRow}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.background = styles.tableRowHover.background;
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'white';
                    }}
                    >
                    <td style={styles.tableCell}>
                        <span style={styles.iataCode}>
                        {airport.iata_code || 'N/A'}
                        </span>
                    </td>
                    <td style={styles.tableCell}>
                        <strong>{airport.name || 'Unknown Airport'}</strong>
                    </td>
                    <td style={styles.tableCell}>{airport.city || 'Unknown'}</td>
                    <td style={styles.tableCell}>{airport.country || 'Unknown'}</td>
                    <td style={styles.tableCell}>
                        {airport.latitude && airport.longitude && airport.latitude !== '' && airport.longitude !== '' ? 
                        `${parseFloat(airport.latitude).toFixed(4)}, ${parseFloat(airport.longitude).toFixed(4)}` : 
                        'No coordinates'
                        }
                    </td>
                    </tr>
                ))}
                </tbody>
            </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
            <div style={styles.pagination}>
                <button
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                style={{
                    ...styles.pageButton,
                    opacity: currentPage === 1 ? 0.5 : 1
                }}
                >
                Previous
                </button>
                
                <span style={styles.pageInfo}>
                Page {currentPage} of {totalPages}
                </span>

                <button
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
                style={{
                    ...styles.pageButton,
                    opacity: currentPage === totalPages ? 0.5 : 1
                }}
                >
                Next
                </button>
            </div>
            )}
        </>
        ) : (
        <div style={styles.emptyState}>
            <div style={styles.emptyIcon}>🏢</div>
            <h3 style={{ color: '#6b7280', marginBottom: '10px' }}>No Airports Found</h3>
            <p style={{ color: '#9ca3af' }}>
            {searchTerm ? 'Try adjusting your search terms' : 'No airports data available'}
            </p>
        </div>
        )}
    </div>
  );
}

export default AirportsList;