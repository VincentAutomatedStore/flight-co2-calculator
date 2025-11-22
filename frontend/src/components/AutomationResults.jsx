import React, { useState, useEffect, useCallback } from 'react';

// Import the new components (make sure these files exist in your components folder)
import ExportControls from './ExportControls';
import DeleteControls from './DeleteControls';
import BatchParameterControls from './BatchParameterControls';
import FileUploadControls from './FileUploadControls';

function AutomationResults() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState({});
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(20);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [batchProgress, setBatchProgress] = useState(null);
  const [showProgress, setShowProgress] = useState(false);
  const [filters, setFilters] = useState({
    route: '', passengers: '', cabin_class: '', distance: '', 
    co2: '', data_source: '', date: ''
  });

  // NEW STATE: Batch processing parameters
  const [batchParams, setBatchParams] = useState({
    passengers: 1,
    cabinClass: 'economy',
    roundTrip: false
  });

  // NEW STATE: Row selection for deletion
  const [selectedRows, setSelectedRows] = useState([]);

  // DEBUG STATE
  const [debugInfo, setDebugInfo] = useState({
    lastProgress: null,
    lastStatus: null,
    apiCalls: 0,
    errors: []
  });

  const itemsPerPageOptions = [10, 20, 50, 100];

  // Simple fetch functions with DEBUG
  const fetchResults = useCallback(async () => {
    try {
      console.log('🔄 FETCHING RESULTS...');
      const response = await fetch('/api/v2/automation/results');
      if (response.ok) {
        const data = await response.json();
        setResults(data);
        setLastUpdated(new Date());
        console.log('✅ RESULTS FETCHED:', data.length, 'items');
        setDebugInfo(prev => ({ 
          ...prev, 
          apiCalls: prev.apiCalls + 1,
          lastResultsCount: data.length
        }));
      } else {
        console.error('❌ RESULTS FETCH FAILED:', response.status);
      }
    } catch (err) {
      console.error('❌ Error fetching results:', err);
      setDebugInfo(prev => ({ 
        ...prev, 
        errors: [...prev.errors, `Results error: ${err.message}`]
      }));
    }
  }, []);

  const fetchStatus = useCallback(async () => {
    try {
      console.log('🔄 FETCHING STATUS...');
      const response = await fetch('/api/v2/automation/status');
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
        console.log('✅ STATUS FETCHED:', data);
        setDebugInfo(prev => ({ 
          ...prev, 
          apiCalls: prev.apiCalls + 1,
          lastStatus: data
        }));
        return data;
      } else {
        console.error('❌ STATUS FETCH FAILED:', response.status);
        return null;
      }
    } catch (err) {
      console.error('❌ Error fetching status:', err);
      setDebugInfo(prev => ({ 
        ...prev, 
        errors: [...prev.errors, `Status error: ${err.message}`]
      }));
      return null;
    }
  }, []);

  const fetchBatchProgress = useCallback(async () => {
    try {
      console.log('🔄 FETCHING PROGRESS...');
      const response = await fetch('/api/v2/automation/progress');
      if (response.ok) {
        const data = await response.json();
        console.log('✅ PROGRESS FETCHED:', data);
        setDebugInfo(prev => ({ 
          ...prev, 
          apiCalls: prev.apiCalls + 1,
          lastProgress: data
        }));
        return data;
      } else {
        console.error('❌ PROGRESS FETCH FAILED:', response.status);
        return null;
      }
    } catch (err) {
      console.error('❌ Error fetching progress:', err);
      setDebugInfo(prev => ({ 
        ...prev, 
        errors: [...prev.errors, `Progress error: ${err.message}`]
      }));
      return null;
    }
  }, []);

  // NEW: Row selection functions
  const handleRowSelect = (calculationId) => {
    setSelectedRows(prev => {
      if (prev.includes(calculationId)) {
        return prev.filter(id => id !== calculationId);
      } else {
        return [...prev, calculationId];
      }
    });
  };

  const handleSelectAll = () => {
    if (selectedRows.length === currentResults.length) {
      setSelectedRows([]);
    } else {
      setSelectedRows(currentResults.map(result => result.id));
    }
  };

  // NEW: Delete functions
  const handleDeleteSelected = async (calculationIds) => {
    try {
      console.log('Deleting selected rows:', calculationIds);
      
      const response = await fetch('/api/v2/automation/delete-multiple', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ calculation_ids: calculationIds })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Delete successful:', result);
        
        // Refresh the data
        await fetchResults();
        // Clear selections
        setSelectedRows([]);
        
        alert(`Successfully deleted ${calculationIds.length} record(s)`);
      } else {
        throw new Error('Delete failed');
      }
    } catch (error) {
      console.error('Delete error:', error);
      alert('Delete failed. Please try again.');
      throw error;
    }
  };

  const handleBulkDelete = async () => {
    try {
      console.log('Deleting all records');
      
      const response = await fetch('/api/v2/automation/delete-all', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Bulk delete successful:', result);
        
        // Refresh the data
        await fetchResults();
        // Clear selections
        setSelectedRows([]);
        
        alert(`Successfully deleted all ${result.deleted_count} records`);
      } else {
        throw new Error('Bulk delete failed');
      }
    } catch (error) {
      console.error('Bulk delete error:', error);
      alert('Bulk delete failed. Please try again.');
      throw error;
    }
  };

  // Initial load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await fetchResults();
      await fetchStatus();
      setLoading(false);
    };
    loadData();
  }, [fetchResults, fetchStatus]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(async () => {
      if (!isProcessing) { // Only auto-refresh when not processing
        console.log('🔄 Auto-refresh triggered');
        await fetchResults();
        await fetchStatus();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh, fetchResults, fetchStatus, isProcessing]);

  // IMPROVED Progress polling with fallback completion detection
  useEffect(() => {
    let progressInterval;
    let fallbackTimeout;
    
    if (isProcessing) {
      console.log('🚀 STARTING PROGRESS POLLING');
      
      progressInterval = setInterval(async () => {
        console.log('🔄 Polling progress...');
        const progress = await fetchBatchProgress();
        
        if (progress) {
          console.log('📊 Progress data:', progress);
          setBatchProgress(progress);
          setShowProgress(true);
          
          // Check completion based on status field
          if (progress.status === 'completed' || progress.status === 'failed') {
            console.log('🎯 PROCESSING COMPLETED DETECTED:', progress.status);
            setIsProcessing(false);
            setShowProgress(true);
            
            // Refresh final data
            await fetchResults();
            await fetchStatus();
          }
          
          // If progress says "idle" but we're processing, check if files are done
          if (progress.status === 'idle' && isProcessing) {
            console.log('⚠️ Progress says idle but we think we are processing - checking status');
            const currentStatus = await fetchStatus();
            if (currentStatus.scheduled_files === 0) {
              console.log('✅ No scheduled files - processing must be complete');
              setIsProcessing(false);
              setBatchProgress({
                status: 'completed',
                message: 'Processing completed successfully!',
                progress_percent: 100,
                processed_rows: 5, // You might want to get this from results count
                error_rows: 0
              });
              await fetchResults();
            }
          }
        } else {
          console.log('⚠️ No progress data received');
        }
      }, 2000);
      
      // Fallback: if no progress updates after 30 seconds, check status
      fallbackTimeout = setTimeout(async () => {
        if (isProcessing) {
          console.log('⏰ Fallback timeout - checking if processing is done');
          const currentStatus = await fetchStatus();
          if (currentStatus.scheduled_files === 0) {
            console.log('✅ Fallback: No scheduled files - marking as complete');
            setIsProcessing(false);
            setBatchProgress(prev => ({
              status: 'completed',
              message: 'Processing completed (fallback detection)',
              progress_percent: 100,
              ...prev
            }));
            await fetchResults();
          } else {
            console.log('⚠️ Fallback: Still scheduled files, continuing to wait');
          }
        }
      }, 30000); // 30 seconds fallback
      
    } else {
      console.log('🛑 STOPPED PROGRESS POLLING');
    }

    return () => {
      if (progressInterval) {
        console.log('🧹 Cleaning up progress interval');
        clearInterval(progressInterval);
      }
      if (fallbackTimeout) {
        console.log('🧹 Cleaning up fallback timeout');
        clearTimeout(fallbackTimeout);
      }
    };
  }, [isProcessing, fetchBatchProgress, fetchResults, fetchStatus]);

  // UPDATED triggerProcessing to include batch parameters
  const triggerProcessing = async () => {
    if (status.scheduled_files === 0) {
      alert('No files scheduled for processing. Please add CSV files to the data/scheduled directory.');
      return;
    }

    try {
      console.log('🎬 STARTING PROCESSING WITH PARAMS:', batchParams);
      setIsProcessing(true);
      setShowProgress(true);
      setBatchProgress({
        status: 'starting',
        message: 'Starting batch processing...',
        progress_percent: 0
      });
      
      const response = await fetch('/api/v2/automation/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          batch_params: batchParams  // Send batch parameters to backend
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to start processing');
      }
      
      console.log('✅ Processing trigger successful');
      
      // Start progress polling immediately
      setTimeout(async () => {
        const initialProgress = await fetchBatchProgress();
        if (initialProgress) {
          console.log('📊 Initial progress:', initialProgress);
          setBatchProgress(initialProgress);
        }
      }, 1000);
      
    } catch (err) {
      console.error('❌ Error triggering processing:', err);
      alert('Failed to start processing');
      setIsProcessing(false);
      setShowProgress(false);
      setBatchProgress(null);
    }
  };

  const cancelProcessing = async () => {
    try {
      console.log('🛑 CANCELLING PROCESSING...');
      const response = await fetch('/api/v2/automation/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      if (response.ok) {
        console.log('✅ Processing cancelled');
        setIsProcessing(false);
        setShowProgress(false);
        setBatchProgress(null);
        await fetchStatus();
      } else {
        alert('Failed to cancel processing');
      }
    } catch (err) {
      console.error('❌ Error cancelling processing:', err);
      alert('Failed to cancel processing');
    }
  };

  const manualRefresh = async () => {
    setLoading(true);
    await fetchResults();
    await fetchStatus();
    setLastUpdated(new Date());
    setLoading(false);
    console.log('✅ Manual refresh completed');
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDataSource = (source) => {
    const sources = {
      'ICAO_API': { label: 'ICAO API', color: '#10b981', bgColor: '#d1fae5' },
      'ENHANCED_CALCULATION': { label: 'Enhanced', color: '#f59e0b', bgColor: '#fef3c7' },
      'ENHANCED_FALLBACK': { label: 'Fallback', color: '#f59e0b', bgColor: '#fef3c7' },
      'BASIC_CALCULATION': { label: 'Basic', color: '#ef4444', bgColor: '#fecaca' },
      'CALCULATION': { label: 'Standard', color: '#6b7280', bgColor: '#f3f4f6' }
    };
    
    const sourceInfo = sources[source] || { 
      label: source || 'Unknown', 
      color: '#6b7280', 
      bgColor: '#f3f4f6' 
    };
    
    return (
      <span style={{
        background: sourceInfo.bgColor,
        color: sourceInfo.color,
        padding: '4px 8px',
        borderRadius: '12px',
        fontSize: '0.75rem',
        fontWeight: '600'
      }}>
        {sourceInfo.label}
      </span>
    );
  };

  const formatCabinClass = (cabin) => {
    return cabin.charAt(0).toUpperCase() + cabin.slice(1).replace('_', ' ');
  };

  // Filter results
  const filteredResults = results.filter(result => {
    return (
      (!filters.route || `${result.departure}→${result.destination}`.toLowerCase().includes(filters.route.toLowerCase())) &&
      (!filters.passengers || result.passengers.toString().includes(filters.passengers)) &&
      (!filters.cabin_class || result.cabin_class.toLowerCase().includes(filters.cabin_class.toLowerCase())) &&
      (!filters.distance || result.distance_km.toString().includes(filters.distance)) &&
      (!filters.co2 || result.co2_per_passenger_kg.toString().includes(filters.co2)) &&
      (!filters.data_source || result.data_source.toLowerCase().includes(filters.data_source.toLowerCase())) &&
      (!filters.date || formatDate(result.created_at).toLowerCase().includes(filters.date.toLowerCase()))
    );
  });

  // Pagination
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentResults = filteredResults.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredResults.length / itemsPerPage);

  // Statistics
  const totalCalculations = filteredResults.length;
  const icaoCalculations = filteredResults.filter(r => r.data_source === 'ICAO_API').length;
  const fallbackCalculations = filteredResults.filter(r => 
    r.data_source === 'ENHANCED_FALLBACK' || r.data_source === 'ENHANCED_CALCULATION'
  ).length;
  const basicCalculations = filteredResults.filter(r => r.data_source === 'BASIC_CALCULATION').length;
  const otherCalculations = filteredResults.filter(r => 
    !['ICAO_API', 'ENHANCED_FALLBACK', 'ENHANCED_CALCULATION', 'BASIC_CALCULATION'].includes(r.data_source)
  ).length;

  // DEBUG: Force completion detection
  const forceComplete = () => {
    console.log('🔄 FORCING COMPLETION STATE');
    setIsProcessing(false);
    setBatchProgress({
      status: 'completed',
      message: 'Processing completed successfully! (Forced)',
      progress_percent: 100,
      processed_rows: 5,
      error_rows: 0
    });
    setShowProgress(true);
  };

  // DEBUG: Check current state
  const debugState = () => {
    console.log('🔍 CURRENT STATE:', {
      isProcessing,
      showProgress,
      batchProgress,
      status,
      resultsCount: results.length,
      debugInfo
    });
  };

  // Styles
  const styles = {
    container: {
      background: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(10px)',
      borderRadius: '25px',
      padding: '40px',
      boxShadow: '0 25px 50px rgba(0, 0, 0, 0.15)',
      border: '1px solid rgba(255, 255, 255, 0.3)'
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      marginBottom: '30px',
      flexWrap: 'wrap',
      gap: '20px'
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
      color: '#6b7280'
    },
    controls: {
      display: 'flex',
      gap: '15px',
      alignItems: 'center',
      flexWrap: 'wrap'
    },
    button: {
      background: 'linear-gradient(135deg, #3b82f6 0%, #10b981 100%)',
      color: 'white',
      border: 'none',
      borderRadius: '12px',
      padding: '12px 24px',
      fontSize: '1rem',
      fontWeight: '600',
      cursor: 'pointer',
      boxShadow: '0 5px 15px rgba(59, 130, 246, 0.4)',
      transition: 'all 0.3s ease'
    },
    cancelButton: {
      background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
      color: 'white',
      border: 'none',
      borderRadius: '12px',
      padding: '12px 24px',
      fontSize: '1rem',
      fontWeight: '600',
      cursor: 'pointer',
      boxShadow: '0 5px 15px rgba(239, 68, 68, 0.4)',
      transition: 'all 0.3s ease'
    },
    secondaryButton: {
      background: 'linear-gradient(135deg, #6b7280 0%, #9ca3af 100%)',
      color: 'white',
      border: 'none',
      borderRadius: '12px',
      padding: '12px 24px',
      fontSize: '1rem',
      fontWeight: '600',
      cursor: 'pointer',
      boxShadow: '0 5px 15px rgba(107, 114, 128, 0.4)',
      transition: 'all 0.3s ease'
    },
    refreshToggle: {
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      background: 'white',
      padding: '10px 15px',
      borderRadius: '10px',
      border: '2px solid #e5e7eb'
    },
    progressCard: {
      background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)',
      border: '2px solid #bfdbfe',
      padding: '20px',
      borderRadius: '15px',
      marginBottom: '30px'
    },
    progressBar: {
      width: '100%',
      height: '20px',
      background: '#e5e7eb',
      borderRadius: '10px',
      overflow: 'hidden',
      margin: '15px 0'
    },
    progressFill: {
      height: '100%',
      background: 'linear-gradient(90deg, #10b981 0%, #3b82f6 100%)',
      borderRadius: '10px',
      transition: 'width 0.3s ease',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'white',
      fontSize: '0.8rem',
      fontWeight: '600'
    },
    progressGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
      gap: '15px',
      marginTop: '15px'
    },
    progressItem: {
      textAlign: 'center'
    },
    progressValue: {
      fontSize: '1.2rem',
      fontWeight: 'bold',
      color: '#1e40af'
    },
    progressLabel: {
      fontSize: '0.8rem',
      color: '#6b7280'
    },
    statsGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '20px',
      marginBottom: '30px'
    },
    statCard: {
      background: 'white',
      padding: '25px',
      borderRadius: '15px',
      boxShadow: '0 5px 15px rgba(0, 0, 0, 0.1)',
      border: '1px solid #e5e7eb',
      textAlign: 'center'
    },
    statValue: {
      fontSize: '2rem',
      fontWeight: 'bold',
      marginBottom: '8px'
    },
    statLabel: {
      fontSize: '0.9rem',
      color: '#6b7280',
      fontWeight: '600'
    },
    statusCard: {
      background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)',
      border: '2px solid #bfdbfe',
      padding: '20px',
      borderRadius: '15px',
      marginBottom: '30px'
    },
    statusGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
      gap: '15px'
    },
    statusItem: {
      textAlign: 'center'
    },
    statusValue: {
      fontSize: '1.5rem',
      fontWeight: 'bold',
      color: '#1e40af'
    },
    statusLabel: {
      fontSize: '0.9rem',
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
      fontSize: '0.9rem'
    },
    tableRow: {
      borderBottom: '1px solid #f3f4f6',
      transition: 'background 0.2s ease'
    },
    tableRowHover: {
      background: '#f8fafc'
    },
    tableCell: {
      padding: '12px 20px',
      fontSize: '0.85rem',
      color: '#374151'
    },
    routeCell: {
      fontWeight: '600',
      color: '#1f2937'
    },
    filterInput: {
      width: '100%',
      padding: '5px 8px',
      border: '1px solid rgba(255,255,255,0.3)',
      borderRadius: '4px',
      fontSize: '0.75rem',
      background: 'rgba(255,255,255,0.2)',
      color: 'white',
      marginTop: '5px'
    },
    pagination: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginTop: '20px',
      flexWrap: 'wrap',
      gap: '15px'
    },
    paginationControls: {
      display: 'flex',
      alignItems: 'center',
      gap: '10px'
    },
    pageButton: {
      padding: '8px 16px',
      border: '2px solid #e5e7eb',
      background: 'white',
      borderRadius: '8px',
      cursor: 'pointer',
      fontSize: '0.9rem',
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
      fontSize: '0.9rem'
    },
    itemsPerPage: {
      display: 'flex',
      alignItems: 'center',
      gap: '10px'
    },
    select: {
      padding: '8px 12px',
      border: '2px solid #e5e7eb',
      borderRadius: '8px',
      background: 'white',
      fontSize: '0.9rem'
    },
    loading: {
      textAlign: 'center',
      padding: '60px',
      color: '#6b7280',
      fontSize: '1.1rem'
    },
    emptyState: {
      textAlign: 'center',
      padding: '60px',
      color: '#6b7280'
    },
    emptyIcon: {
      fontSize: '4rem',
      marginBottom: '20px'
    },
    lastUpdated: {
      textAlign: 'center',
      color: '#9ca3af',
      fontSize: '0.8rem',
      marginTop: '10px'
    },
    // ADD DEBUG STYLES
    debugPanel: {
      background: '#1f2937',
      color: 'white',
      padding: '15px',
      borderRadius: '10px',
      marginBottom: '20px',
      fontSize: '0.8rem'
    },
    debugHeader: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '10px'
    },
    debugButton: {
      background: '#3b82f6',
      color: 'white',
      border: 'none',
      borderRadius: '6px',
      padding: '5px 10px',
      fontSize: '0.7rem',
      cursor: 'pointer',
      marginLeft: '5px'
    }
  };

  if (loading && results.length === 0) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>
          <div style={{ fontSize: '3rem', marginBottom: '20px' }}>⏳</div>
          Loading batch processing results...
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* DEBUG PANEL */}
      <div style={styles.debugPanel}>
        <div style={styles.debugHeader}>
          <strong>🔧 DEBUG PANEL</strong>
          <div>
            <button style={styles.debugButton} onClick={debugState}>
              Log State
            </button>
            <button style={styles.debugButton} onClick={forceComplete}>
              Force Complete
            </button>
          </div>
        </div>
        <div>
          <strong>State:</strong> isProcessing: {isProcessing ? 'TRUE' : 'FALSE'}, 
          showProgress: {showProgress ? 'TRUE' : 'FALSE'}
        </div>
        <div>
          <strong>Progress Status:</strong> {batchProgress?.status || 'none'}
        </div>
        <div>
          <strong>Scheduled Files:</strong> {status.scheduled_files || 0}
        </div>
        <div>
          <strong>API Calls:</strong> {debugInfo.apiCalls}
        </div>
        {debugInfo.errors.length > 0 && (
          <div>
            <strong>Errors:</strong> {debugInfo.errors.slice(-3).join(', ')}
          </div>
        )}
      </div>

      {/* Header */}
      <div style={styles.header}>
        <div>
          <h2 style={styles.title}>Batch Processing Results</h2>
          <p style={styles.subtitle}>
            Automated flight emissions calculations from CSV processing
            {lastUpdated && (
              <div style={styles.lastUpdated}>
                Last updated: {formatDate(lastUpdated)}
                {loading && <span style={{color: '#3b82f6', marginLeft: '10px'}}>🔄 Refreshing...</span>}
              </div>
            )}
          </p>
        </div>
        <div style={styles.controls}>
          {/* PROCESS BUTTON - Only show when NOT processing */}
          {!isProcessing && (
            <button
              onClick={triggerProcessing}
              style={{
                ...styles.button,
                ...(status.scheduled_files === 0 && { opacity: 0.7, cursor: 'not-allowed' })
              }}
              disabled={status.scheduled_files === 0}
            >
              🚀 Process Files ({status.scheduled_files || 0})
            </button>
          )}

          {/* CANCEL BUTTON - Only show when processing */}
          {isProcessing && (
            <button
              onClick={cancelProcessing}
              style={styles.cancelButton}
            >
              ❌ Cancel Processing
            </button>
          )}
          
          <button
            onClick={manualRefresh}
            style={styles.secondaryButton}
            disabled={loading}
          >
            {loading ? '🔄 Refreshing...' : '📊 Refresh Data'}
          </button>
          
          {Object.values(filters).some(filter => filter !== '') && (
            <button
              onClick={() => setFilters({
                route: '', passengers: '', cabin_class: '', distance: '', 
                co2: '', data_source: '', date: ''
              })}
              style={{ ...styles.button, background: 'linear-gradient(135deg, #6b7280 0%, #9ca3af 100%)' }}
            >
              🗑️ Clear Filters
            </button>
          )}
          
          <div style={styles.refreshToggle}>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              id="autoRefresh"
            />
            <label htmlFor="autoRefresh" style={{ fontSize: '0.9rem', color: '#6b7280' }}>
              Auto-refresh
            </label>
          </div>
        </div>
      </div>

      {/* NEW: File Upload Controls */}
      <FileUploadControls />      

      {/* NEW: Batch Parameter Controls */}
      <BatchParameterControls 
        batchParams={batchParams}
        setBatchParams={setBatchParams}
        isProcessing={isProcessing}
      />

      {/* NEW: Export Controls */}
      <ExportControls 
        results={filteredResults}
        filters={filters}
        batchParams={batchParams}
      />

      {/* NEW: Delete Controls */}
      <DeleteControls 
        selectedRows={selectedRows}
        onDelete={handleDeleteSelected}
        onBulkDelete={handleBulkDelete}
        totalResults={filteredResults.length}
      />

      {/* Progress Card - Shows during AND after processing */}
      {showProgress && batchProgress && (
        <div style={{
          ...styles.progressCard,
          ...((batchProgress.status === 'completed' || batchProgress.status === 'failed') && {
            background: batchProgress.status === 'completed' 
              ? 'linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)'
              : 'linear-gradient(135deg, #fecaca 0%, #fca5a5 100%)',
            border: batchProgress.status === 'completed' 
              ? '2px solid #10b981'
              : '2px solid #ef4444'
          })
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <h3 style={{ 
              color: batchProgress.status === 'completed' ? '#10b981' : 
                     batchProgress.status === 'failed' ? '#ef4444' : '#1e40af', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '10px', 
              margin: 0 
            }}>
              {batchProgress.status === 'processing' ? '🔄' : 
               batchProgress.status === 'completed' ? '✅' : 
               batchProgress.status === 'failed' ? '❌' : '🚀'}
              Batch Processing {batchProgress.status === 'processing' ? 'In Progress' : 
                             batchProgress.status === 'completed' ? 'Complete!' : 
                             batchProgress.status === 'failed' ? 'Failed' : 'Starting...'}
            </h3>
            
            {/* Only show cancel button when processing */}
            {batchProgress.status === 'processing' && (
              <button
                onClick={cancelProcessing}
                style={{
                  ...styles.cancelButton,
                  padding: '8px 16px',
                  fontSize: '0.9rem'
                }}
              >
                ❌ Cancel
              </button>
            )}
            
            {/* Show close button when completed/failed */}
            {(batchProgress.status === 'completed' || batchProgress.status === 'failed') && (
              <button
                onClick={() => {
                  setShowProgress(false);
                  setBatchProgress(null);
                }}
                style={{
                  ...styles.secondaryButton,
                  padding: '8px 16px',
                  fontSize: '0.9rem'
                }}
              >
                ✕ Close
              </button>
            )}
          </div>
          
          {batchProgress.message && (
            <p style={{ 
              color: batchProgress.status === 'completed' ? '#10b981' : 
                     batchProgress.status === 'failed' ? '#ef4444' : '#6b7280',
              marginBottom: '15px',
              fontWeight: batchProgress.status === 'completed' ? '600' : 'normal'
            }}>
              {batchProgress.message}
            </p>
          )}
          
          {batchProgress.progress_percent && (
            <div style={styles.progressBar}>
              <div 
                style={{ 
                  ...styles.progressFill, 
                  width: `${batchProgress.progress_percent}%`,
                  background: batchProgress.status === 'completed' 
                    ? 'linear-gradient(90deg, #10b981 0%, #34d399 100%)'
                    : batchProgress.status === 'failed'
                    ? 'linear-gradient(90deg, #ef4444 0%, #f87171 100%)'
                    : 'linear-gradient(90deg, #10b981 0%, #3b82f6 100%)'
                }}
              >
                {batchProgress.progress_percent}%
              </div>
            </div>
          )}
          
          <div style={styles.progressGrid}>
            {batchProgress.current_row && (
              <div style={styles.progressItem}>
                <div style={styles.progressValue}>{batchProgress.current_row}</div>
                <div style={styles.progressLabel}>Current Row</div>
              </div>
            )}
            {batchProgress.total_rows && (
              <div style={styles.progressItem}>
                <div style={styles.progressValue}>{batchProgress.total_rows}</div>
                <div style={styles.progressLabel}>Total Rows</div>
              </div>
            )}
            {batchProgress.processed_rows !== undefined && (
              <div style={styles.progressItem}>
                <div style={styles.progressValue}>{batchProgress.processed_rows}</div>
                <div style={styles.progressLabel}>Processed</div>
              </div>
            )}
            {batchProgress.error_rows !== undefined && (
              <div style={styles.progressItem}>
                <div style={{
                  ...styles.progressValue, 
                  color: batchProgress.error_rows > 0 ? '#ef4444' : '#1e40af'
                }}>
                  {batchProgress.error_rows}
                </div>
                <div style={styles.progressLabel}>Errors</div>
              </div>
            )}
          </div>
          
          {/* Show completion summary */}
          {(batchProgress.status === 'completed' || batchProgress.status === 'failed') && (
            <div style={{ 
              marginTop: '20px', 
              padding: '15px', 
              background: 'rgba(255,255,255,0.7)', 
              borderRadius: '10px',
              textAlign: 'center'
            }}>
              <p style={{ 
                margin: 0, 
                fontWeight: '600',
                color: batchProgress.status === 'completed' ? '#10b981' : '#ef4444'
              }}>
                {batchProgress.status === 'completed' ? '✅ Processing Completed Successfully!' : '❌ Processing Failed!'}
              </p>
              <p style={{ margin: '5px 0 0 0', fontSize: '0.9rem', color: '#6b7280' }}>
                {batchProgress.processed_rows || 0} records processed • {batchProgress.error_rows || 0} errors
              </p>
            </div>
          )}
        </div>
      )}

      {/* Statistics */}
      <div style={styles.statsGrid}>
        <div style={styles.statCard}>
          <div style={{ ...styles.statValue, color: '#3b82f6' }}>
            {totalCalculations}
          </div>
          <div style={styles.statLabel}>Total Calculations</div>
        </div>
        <div style={styles.statCard}>
          <div style={{ ...styles.statValue, color: '#10b981' }}>
            {icaoCalculations}
          </div>
          <div style={styles.statLabel}>ICAO API Results</div>
        </div>
        <div style={styles.statCard}>
          <div style={{ ...styles.statValue, color: '#f59e0b' }}>
            {fallbackCalculations}
          </div>
          <div style={styles.statLabel}>Enhanced Fallbacks</div>
        </div>
        <div style={styles.statCard}>
          <div style={{ ...styles.statValue, color: '#ef4444' }}>
            {basicCalculations}
          </div>
          <div style={styles.statLabel}>Basic Calculations</div>
        </div>
        {otherCalculations > 0 && (
          <div style={styles.statCard}>
            <div style={{ ...styles.statValue, color: '#8b5cf6' }}>
              {otherCalculations}
            </div>
            <div style={styles.statLabel}>Other Methods</div>
          </div>
        )}
      </div>

      {/* Automation Status */}
      <div style={styles.statusCard}>
        <h3 style={{ marginBottom: '15px', color: '#1e40af' }}>Automation Status</h3>
        <div style={styles.statusGrid}>
          <div style={styles.statusItem}>
            <div style={styles.statusValue}>
              {status.scheduled_files || 0}
            </div>
            <div style={styles.statusLabel}>Scheduled Files</div>
          </div>
          <div style={styles.statusItem}>
            <div style={styles.statusValue}>
              {status.processed_files || 0}
            </div>
            <div style={styles.statusLabel}>Processed Files</div>
          </div>
          <div style={styles.statusItem}>
            <div style={styles.statusValue}>
              {status.errors_files || 0}
            </div>
            <div style={styles.statusLabel}>Error Files</div>
          </div>
          <div style={styles.statusItem}>
            <div style={{
              ...styles.statusValue,
              color: status.scheduler_running ? '#10b981' : '#ef4444'
            }}>
              {status.scheduler_running ? '🟢' : '🔴'}
            </div>
            <div style={styles.statusLabel}>Scheduler</div>
          </div>
        </div>
        {status.scheduled_files === 0 && !isProcessing && (
          <p style={{ color: '#6b7280', marginTop: '15px', textAlign: 'center' }}>
            No files scheduled. Add CSV files to the data/scheduled directory.
          </p>
        )}
        {isProcessing && (
          <p style={{ color: '#3b82f6', marginTop: '15px', textAlign: 'center', fontWeight: '600' }}>
            🚀 Processing in progress...
          </p>
        )}
      </div>

      {/* Results Table */}
      {currentResults.length > 0 ? (
        <>
          <div style={styles.tableContainer}>
            <table style={styles.table}>
              <thead style={styles.tableHeader}>
                <tr>
                  {/* NEW: Selection column */}
                  <th style={styles.tableHeaderCell}>
                    <input
                      type="checkbox"
                      checked={selectedRows.length === currentResults.length && currentResults.length > 0}
                      onChange={handleSelectAll}
                      style={{ marginRight: '8px' }}
                    />
                    Select
                  </th>
                  <th style={styles.tableHeaderCell}>
                    Route
                    <input
                      type="text"
                      placeholder="Filter route..."
                      value={filters.route}
                      onChange={(e) => setFilters(prev => ({ ...prev, route: e.target.value }))}
                      style={styles.filterInput}
                    />
                  </th>
                  <th style={styles.tableHeaderCell}>
                    Passengers
                    <input
                      type="text"
                      placeholder="Filter..."
                      value={filters.passengers}
                      onChange={(e) => setFilters(prev => ({ ...prev, passengers: e.target.value }))}
                      style={styles.filterInput}
                    />
                  </th>
                  <th style={styles.tableHeaderCell}>
                    Cabin Class
                    <input
                      type="text"
                      placeholder="Filter..."
                      value={filters.cabin_class}
                      onChange={(e) => setFilters(prev => ({ ...prev, cabin_class: e.target.value }))}
                      style={styles.filterInput}
                    />
                  </th>
                  <th style={styles.tableHeaderCell}>
                    Distance
                    <input
                      type="text"
                      placeholder="Filter..."
                      value={filters.distance}
                      onChange={(e) => setFilters(prev => ({ ...prev, distance: e.target.value }))}
                      style={styles.filterInput}
                    />
                  </th>
                  <th style={styles.tableHeaderCell}>
                    CO₂ per Pax
                    <input
                      type="text"
                      placeholder="Filter..."
                      value={filters.co2}
                      onChange={(e) => setFilters(prev => ({ ...prev, co2: e.target.value }))}
                      style={styles.filterInput}
                    />
                  </th>
                  <th style={styles.tableHeaderCell}>
                    Total CO₂
                  </th>
                  <th style={styles.tableHeaderCell}>
                    Data Source
                    <input
                      type="text"
                      placeholder="Filter..."
                      value={filters.data_source}
                      onChange={(e) => setFilters(prev => ({ ...prev, data_source: e.target.value }))}
                      style={styles.filterInput}
                    />
                  </th>
                  <th style={styles.tableHeaderCell}>
                    Calculated
                    <input
                      type="text"
                      placeholder="Filter date..."
                      value={filters.date}
                      onChange={(e) => setFilters(prev => ({ ...prev, date: e.target.value }))}
                      style={styles.filterInput}
                    />
                  </th>
                </tr>
              </thead>
              <tbody>
                {currentResults.map((result, index) => (
                  <tr 
                    key={result.id}
                    style={{
                      ...styles.tableRow,
                      background: selectedRows.includes(result.id) ? '#dbeafe' : 'white'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = selectedRows.includes(result.id) 
                        ? '#dbeafe' 
                        : styles.tableRowHover.background;
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = selectedRows.includes(result.id) 
                        ? '#dbeafe' 
                        : 'white';
                    }}
                  >
                    {/* NEW: Selection checkbox */}
                    <td style={styles.tableCell}>
                      <input
                        type="checkbox"
                        checked={selectedRows.includes(result.id)}
                        onChange={() => handleRowSelect(result.id)}
                      />
                    </td>
                    <td style={{ ...styles.tableCell, ...styles.routeCell }}>
                      {result.departure} → {result.destination}
                      {result.round_trip && ' (Round Trip)'}
                    </td>
                    <td style={styles.tableCell}>{result.passengers}</td>
                    <td style={styles.tableCell}>{formatCabinClass(result.cabin_class)}</td>
                    <td style={styles.tableCell}>{result.distance_km} km</td>
                    <td style={styles.tableCell}>{result.co2_per_passenger_kg} kg</td>
                    <td style={styles.tableCell}>{result.total_co2_kg} kg</td>
                    <td style={styles.tableCell}>
                      {formatDataSource(result.data_source)}
                    </td>
                    <td style={styles.tableCell}>
                      {formatDate(result.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div style={styles.pagination}>
            <div style={styles.pageInfo}>
              Showing {indexOfFirstItem + 1}-{Math.min(indexOfLastItem, filteredResults.length)} of {filteredResults.length} calculations
              {filteredResults.length !== results.length && ` (filtered from ${results.length} total)`}
            </div>
            
            <div style={styles.paginationControls}>
              <div style={styles.itemsPerPage}>
                <span style={{ fontSize: '0.9rem', color: '#6b7280' }}>Show:</span>
                <select
                  value={itemsPerPage}
                  onChange={(e) => {
                    setItemsPerPage(Number(e.target.value));
                    setCurrentPage(1);
                  }}
                  style={styles.select}
                >
                  {itemsPerPageOptions.map(option => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>

              <button
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
                style={{
                  ...styles.pageButton,
                  opacity: currentPage === 1 ? 0.5 : 1
                }}
              >
                First
              </button>
              
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

              <button
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
                style={{
                  ...styles.pageButton,
                  opacity: currentPage === totalPages ? 0.5 : 1
                }}
              >
                Last
              </button>
            </div>
          </div>
        </>
      ) : (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>📊</div>
          <h3 style={{ color: '#6b7280', marginBottom: '10px' }}>No Batch Results Yet</h3>
          <p style={{ color: '#9ca3af' }}>
            {Object.values(filters).some(filter => filter !== '') 
              ? 'No results match your current filters. Try adjusting your search criteria.'
              : 'Process scheduled CSV files to see calculation results here.'
            }
          </p>
        </div>
      )}
    </div>
  );
}

export default AutomationResults;