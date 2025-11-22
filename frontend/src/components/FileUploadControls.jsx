import React, { useState } from 'react';

function FileUploadControls() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    console.log('File selected:', file); // Debug log
    
    if (file) {
      // More flexible file type checking
      const isCSV = file.type === 'text/csv' || 
                   file.name.toLowerCase().endsWith('.csv') ||
                   file.type === 'application/vnd.ms-excel';
      
      console.log('File type:', file.type, 'Is CSV:', isCSV); // Debug log
      
      if (isCSV) {
        setSelectedFile(file);
        setUploadStatus('');
      } else {
        setSelectedFile(null);
        setUploadStatus('Please select a valid CSV file. File type: ' + file.type);
      }
    } else {
      setSelectedFile(null);
      setUploadStatus('No file selected');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadStatus('Uploading...');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      console.log('Starting upload...'); // Debug log
      
      const response = await fetch('/api/v2/automation/upload-csv', {
        method: 'POST',
        body: formData,
        // Don't set Content-Type header - let browser set it with boundary
      });

      console.log('Upload response status:', response.status); // Debug log
      
      if (response.ok) {
        const result = await response.json();
        console.log('Upload success:', result); // Debug log
        setUploadStatus(`✅ ${result.message}`);
        setSelectedFile(null);
        // Clear file input
        document.getElementById('csv-file-input').value = '';
        
        // Refresh the page after 2 seconds to show updated file count
        setTimeout(() => {
          window.location.reload();
        }, 2000);
      } else {
        const error = await response.json();
        console.error('Upload failed:', error); // Debug log
        setUploadStatus(`❌ Upload failed: ${error.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadStatus('❌ Upload failed. Please check console for details.');
    } finally {
      setUploading(false);
    }
  };

  const styles = {
    container: {
      background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)',
      border: '2px solid #bfdbfe',
      padding: '20px',
      borderRadius: '15px',
      marginBottom: '20px'
    },
    title: {
      color: '#1e40af',
      marginBottom: '15px',
      display: 'flex',
      alignItems: 'center',
      gap: '10px'
    },
    controls: {
      display: 'flex',
      gap: '15px',
      alignItems: 'flex-end',
      flexWrap: 'wrap'
    },
    fileInput: {
      flex: '1',
      minWidth: '200px'
    },
    input: {
      width: '98%',
      padding: '10px',
      border: '2px solid #d1d5db',
      borderRadius: '8px',
      fontSize: '0.9rem',
      background: 'white'
    },
    uploadButton: {
      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
      color: 'white',
      border: 'none',
      borderRadius: '8px',
      padding: '10px 20px',
      fontSize: '0.9rem',
      fontWeight: '600',
      cursor: 'pointer',
      boxShadow: '0 4px 6px rgba(5, 150, 105, 0.3)',
      transition: 'all 0.3s ease',
      whiteSpace: 'nowrap',
      minWidth: '120px'
    },
    uploadButtonDisabled: {
      background: 'linear-gradient(135deg, #9ca3af 0%, #6b7280 100%)',
      cursor: 'not-allowed',
      opacity: 0.6
    },
    uploadButtonHover: {
      transform: 'translateY(-2px)',
      boxShadow: '0 6px 8px rgba(5, 150, 105, 0.4)'
    },
    status: {
      marginTop: '10px',
      padding: '8px 12px',
      borderRadius: '6px',
      fontSize: '0.85rem',
      fontWeight: '500'
    },
    statusSuccess: {
      background: '#d1fae5',
      color: '#065f46',
      border: '1px solid #a7f3d0'
    },
    statusError: {
      background: '#fecaca',
      color: '#991b1b',
      border: '1px solid #fca5a5'
    },
    statusInfo: {
      background: '#dbeafe',
      color: '#1e40af',
      border: '1px solid #93c5fd'
    },
    fileInfo: {
      marginTop: '8px',
      fontSize: '0.8rem',
      color: '#6b7280',
      background: 'white',
      padding: '8px',
      borderRadius: '4px',
      border: '1px solid #e5e7eb'
    },
    debugInfo: {
      marginTop: '10px',
      padding: '10px',
      background: '#f3f4f6',
      borderRadius: '6px',
      fontSize: '0.75rem',
      color: '#6b7280',
      border: '1px solid #e5e7eb'
    }
  };

  const getStatusStyle = () => {
    if (uploadStatus.includes('✅')) return { ...styles.status, ...styles.statusSuccess };
    if (uploadStatus.includes('❌')) return { ...styles.status, ...styles.statusError };
    return { ...styles.status, ...styles.statusInfo };
  };

  const isUploadDisabled = !selectedFile || uploading;

  return (
    <div style={styles.container}>
      <h3 style={styles.title}>
        📤 Upload Schedule CSV
      </h3>
      
      <div style={styles.controls}>
        <div style={styles.fileInput}>
          <input
            id="csv-file-input"
            type="file"
            accept=".csv,text/csv"
            onChange={handleFileSelect}
            style={styles.input}
            disabled={uploading}
          />
          {selectedFile && (
            <div style={styles.fileInfo}>
              <strong>Selected file:</strong> {selectedFile.name}<br />
              <strong>Size:</strong> {Math.round(selectedFile.size / 1024)} KB<br />
              <strong>Type:</strong> {selectedFile.type || 'Unknown'}
            </div>
          )}
        </div>
        
        <button
          onClick={handleUpload}
          disabled={isUploadDisabled}
          style={{
            ...styles.uploadButton,
            ...(isUploadDisabled && styles.uploadButtonDisabled),
            ...(!isUploadDisabled && styles.uploadButtonHover)
          }}
          onMouseEnter={(e) => {
            if (!isUploadDisabled) {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 6px 8px rgba(5, 150, 105, 0.4)';
            }
          }}
          onMouseLeave={(e) => {
            if (!isUploadDisabled) {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 4px 6px rgba(5, 150, 105, 0.3)';
            }
          }}
        >
          {uploading ? '📤 Uploading...' : '🚀 Upload CSV'}
        </button>
      </div>

      {uploadStatus && (
        <div style={getStatusStyle()}>
          {uploadStatus}
        </div>
      )}

      {/* Debug information - remove in production */}
      <div style={styles.debugInfo}>
        <strong>Debug Info:</strong><br />
        Selected File: {selectedFile ? selectedFile.name : 'None'}<br />
        Uploading: {uploading ? 'Yes' : 'No'}<br />
        Button Disabled: {isUploadDisabled ? 'Yes' : 'No'}
      </div>

      <div style={{ marginTop: '15px', fontSize: '0.8rem', color: '#6b7280' }}>
        <strong>CSV Format:</strong> departure_iata,destination_iata<br />
        <strong>Example:</strong> DUB,DOH<br />
        <strong>Expected location:</strong> <code>backend/data/scheduled/</code>
      </div>
    </div>
  );
}

export default FileUploadControls;