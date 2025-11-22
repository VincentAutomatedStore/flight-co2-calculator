import React, { useState } from 'react';

const ExportControls = ({ results, filters, batchParams }) => {
  const [exporting, setExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState('csv');

  // NEW: Separate function for quick exports that takes the format as parameter
  const handleQuickExport = async (format) => {
    if (!results || results.length === 0) {
      alert('No data to export');
      return;
    }

    setExporting(true);
    try {
      const response = await fetch('/api/v2/automation/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          format: format, // Use the passed format, not the state
          data: results,
          filters: filters,
          batchParams: batchParams,
          timestamp: new Date().toISOString()
        })
      });

      if (response.ok) {
        if (format === 'sql') {
          // For SQL, we get a JSON response with the SQL content
          const sqlData = await response.json();
          downloadSQLFile(sqlData);
        } else {
          // For other formats, we get a file blob
          const blob = await response.blob();
          downloadFile(blob, format); // Use the passed format
        }
      } else {
        throw new Error('Export failed');
      }
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  // Keep the original handleExport for the main export button
  const handleExport = async () => {
    await handleQuickExport(exportFormat);
  };

  const downloadFile = (blob, format) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    
    const timestamp = new Date().toISOString().split('T')[0];
    const extensions = {
      'csv': 'csv',
      'excel': 'xlsx',
      'pdf': 'pdf'
    };
    const filename = `flight_emissions_${timestamp}.${extensions[format]}`;
    a.download = filename;
    
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const downloadSQLFile = (sqlData) => {
    const blob = new Blob([sqlData.sql_content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = sqlData.filename;
    
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const exportOptions = [
    { value: 'csv', label: 'CSV', icon: '📊' },
    { value: 'excel', label: 'Excel', icon: '📈' },
    { value: 'pdf', label: 'PDF', icon: '📄' },
    { value: 'sql', label: 'SQL Server', icon: '🗃️' }
  ];

  return (
    <div style={{
      background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)',
      border: '2px solid #bfdbfe',
      borderRadius: '15px',
      padding: '20px',
      marginBottom: '25px'
    }}>
      <h3 style={{
        margin: '0 0 15px 0',
        color: '#1e40af',
        fontSize: '1.2rem',
        fontWeight: '600',
        display: 'flex',
        alignItems: 'center',
        gap: '10px'
      }}>
        📤 Export Results
      </h3>
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '15px',
        alignItems: 'end'
      }}>
        {/* Format Selection */}
        <div>
          <label style={{
            display: 'block',
            marginBottom: '8px',
            fontWeight: '600',
            color: '#374151',
            fontSize: '0.9rem'
          }}>
            Export Format
          </label>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '8px'
          }}>
            {exportOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setExportFormat(option.value)}
                style={{
                  padding: '10px 8px',
                  border: `2px solid ${
                    exportFormat === option.value ? '#3b82f6' : '#d1d5db'
                  }`,
                  borderRadius: '8px',
                  background: exportFormat === option.value ? '#dbeafe' : 'white',
                  color: exportFormat === option.value ? '#1e40af' : '#374151',
                  fontSize: '0.8rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                <div style={{ fontSize: '1.2rem', marginBottom: '4px' }}>
                  {option.icon}
                </div>
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {/* Export Info */}
        <div style={{
          padding: '12px',
          background: 'rgba(59, 130, 246, 0.1)',
          borderRadius: '8px',
          border: '1px solid #3b82f6'
        }}>
          <div style={{
            fontSize: '0.8rem',
            color: '#1e40af',
            fontWeight: '600',
            marginBottom: '4px'
          }}>
            📋 Export Details
          </div>
          <div style={{
            fontSize: '0.75rem',
            color: '#374151'
          }}>
            {results.length} records • {exportFormat.toUpperCase()} format
            {exportFormat === 'sql' && ' • INSERT statements'}
          </div>
        </div>

        {/* Export Button */}
        <div>
          <button
            onClick={handleExport}
            disabled={exporting || !results || results.length === 0}
            style={{
              width: '100%',
              padding: '12px 16px',
              background: exportFormat === 'sql' 
                ? 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)' 
                : 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '0.9rem',
              fontWeight: '600',
              cursor: exporting || !results || results.length === 0 ? 'not-allowed' : 'pointer',
              opacity: exporting || !results || results.length === 0 ? 0.6 : 1,
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
          >
            {exporting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Exporting...
              </>
            ) : (
              <>
                {exportFormat === 'sql' ? '🗃️' : '📥'} Export {exportFormat.toUpperCase()}
              </>
            )}
          </button>
        </div>
      </div>

      {/* Quick Export Options - FIXED */}
      <div style={{
        marginTop: '15px',
        paddingTop: '15px',
        borderTop: '1px solid #d1d5db'
      }}>
        <div style={{
          fontSize: '0.8rem',
          color: '#6b7280',
          marginBottom: '8px',
          fontWeight: '600'
        }}>
          Quick Export:
        </div>
        <div style={{
          display: 'flex',
          gap: '10px',
          flexWrap: 'wrap'
        }}>
          {/* FIXED: Use handleQuickExport with explicit format */}
          <button
            onClick={() => handleQuickExport('csv')}
            disabled={exporting || !results || results.length === 0}
            style={{
              padding: '6px 12px',
              background: '#f3f4f6',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '0.75rem',
              cursor: exporting || !results || results.length === 0 ? 'not-allowed' : 'pointer',
              opacity: exporting || !results || results.length === 0 ? 0.5 : 1
            }}
          >
            📊 Quick CSV
          </button>
          <button
            onClick={() => handleQuickExport('excel')}
            disabled={exporting || !results || results.length === 0}
            style={{
              padding: '6px 12px',
              background: '#f3f4f6',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '0.75rem',
              cursor: exporting || !results || results.length === 0 ? 'not-allowed' : 'pointer',
              opacity: exporting || !results || results.length === 0 ? 0.5 : 1
            }}
          >
            📈 Quick Excel
          </button>
          <button
            onClick={() => handleQuickExport('sql')}
            disabled={exporting || !results || results.length === 0}
            style={{
              padding: '6px 12px',
              background: '#f3f4f6',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '0.75rem',
              cursor: exporting || !results || results.length === 0 ? 'not-allowed' : 'pointer',
              opacity: exporting || !results || results.length === 0 ? 0.5 : 1
            }}
          >
            🗃️ Quick SQL
          </button>
          <button
            onClick={() => handleQuickExport('pdf')}
            disabled={exporting || !results || results.length === 0}
            style={{
              padding: '6px 12px',
              background: '#f3f4f6',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '0.75rem',
              cursor: exporting || !results || results.length === 0 ? 'not-allowed' : 'pointer',
              opacity: exporting || !results || results.length === 0 ? 0.5 : 1
            }}
          >
            📄 Quick PDF
          </button>
        </div>
      </div>

      {/* SQL Export Info */}
      {exportFormat === 'sql' && (
        <div style={{
          marginTop: '15px',
          padding: '12px',
          background: 'rgba(139, 92, 246, 0.1)',
          borderRadius: '8px',
          border: '1px solid #8b5cf6'
        }}>
          <div style={{
            fontSize: '0.8rem',
            color: '#7c3aed',
            fontWeight: '600',
            marginBottom: '4px'
          }}>
            💡 SQL Server Export
          </div>
          <div style={{
            fontSize: '0.75rem',
            color: '#6b7280'
          }}>
            Generates INSERT statements for SQL Server migration. Includes identity insert handling and data validation.
          </div>
        </div>
      )}
    </div>
  );
};

export default ExportControls;