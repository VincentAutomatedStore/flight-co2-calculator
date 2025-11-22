import React, { useState } from 'react';

const DeleteControls = ({ selectedRows, onDelete, onBulkDelete, totalResults }) => {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteType, setDeleteType] = useState(''); // 'selected' or 'all'
  const [deleting, setDeleting] = useState(false);

  const handleDeleteClick = (type) => {
    setDeleteType(type);
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = async () => {
    setDeleting(true);
    try {
      if (deleteType === 'selected') {
        await onDelete(selectedRows);
      } else {
        await onBulkDelete();
      }
      setShowDeleteConfirm(false);
    } catch (error) {
      console.error('Delete error:', error);
      alert('Delete failed. Please try again.');
    } finally {
      setDeleting(false);
    }
  };

  const selectedCount = selectedRows.length;
  const hasSelections = selectedCount > 0;

  return (
    <>
      <div style={{
        background: 'linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)',
        border: '2px solid #fecaca',
        borderRadius: '15px',
        padding: '20px',
        marginBottom: '25px'
      }}>
        <h3 style={{
          margin: '0 0 15px 0',
          color: '#dc2626',
          fontSize: '1.2rem',
          fontWeight: '600',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          🗑️ Data Management
        </h3>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '15px',
          alignItems: 'end'
        }}>
          {/* Selected Rows Delete */}
          <div>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              fontWeight: '600',
              color: '#374151',
              fontSize: '0.9rem'
            }}>
              Delete Selected Rows
            </label>
            <button
              onClick={() => handleDeleteClick('selected')}
              disabled={!hasSelections || deleting}
              style={{
                width: '100%',
                padding: '12px 16px',
                background: hasSelections 
                  ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
                  : 'linear-gradient(135deg, #9ca3af 0%, #6b7280 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '0.9rem',
                fontWeight: '600',
                cursor: hasSelections && !deleting ? 'pointer' : 'not-allowed',
                opacity: deleting ? 0.6 : 1,
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
            >
              {deleting && deleteType === 'selected' ? (
                <>
                  <div style={{ 
                    width: '16px', 
                    height: '16px', 
                    border: '2px solid white', 
                    borderTop: '2px solid transparent',
                    borderRadius: '50%', 
                    animation: 'spin 1s linear infinite' 
                  }} />
                  Deleting...
                </>
              ) : (
                <>
                  🗑️ Delete Selected ({selectedCount})
                </>
              )}
            </button>
            <div style={{
              fontSize: '0.75rem',
              color: '#6b7280',
              marginTop: '8px',
              textAlign: 'center'
            }}>
              {hasSelections ? `${selectedCount} rows selected` : 'No rows selected'}
            </div>
          </div>

          {/* Bulk Delete All */}
          <div>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              fontWeight: '600',
              color: '#374151',
              fontSize: '0.9rem'
            }}>
              Delete All Data
            </label>
            <button
              onClick={() => handleDeleteClick('all')}
              disabled={totalResults === 0 || deleting}
              style={{
                width: '100%',
                padding: '12px 16px',
                background: totalResults > 0
                  ? 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)'
                  : 'linear-gradient(135deg, #9ca3af 0%, #6b7280 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '0.9rem',
                fontWeight: '600',
                cursor: totalResults > 0 && !deleting ? 'pointer' : 'not-allowed',
                opacity: deleting ? 0.6 : 1,
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
            >
              {deleting && deleteType === 'all' ? (
                <>
                  <div style={{ 
                    width: '16px', 
                    height: '16px', 
                    border: '2px solid white', 
                    borderTop: '2px solid transparent',
                    borderRadius: '50%', 
                    animation: 'spin 1s linear infinite' 
                  }} />
                  Deleting All...
                </>
              ) : (
                <>
                  💥 Delete All ({totalResults})
                </>
              )}
            </button>
            <div style={{
              fontSize: '0.75rem',
              color: '#6b7280',
              marginTop: '8px',
              textAlign: 'center'
            }}>
              {totalResults > 0 ? `${totalResults} total records` : 'No data to delete'}
            </div>
          </div>

          {/* Quick Actions */}
          {/* <div style={{
            padding: '12px',
            background: 'rgba(239, 68, 68, 0.1)',
            borderRadius: '8px',
            border: '1px solid #ef4444'
          }}>
            <div style={{
              fontSize: '0.8rem',
              color: '#dc2626',
              fontWeight: '600',
              marginBottom: '4px'
            }}>
              ⚡ Quick Actions
            </div>
            <div style={{
              fontSize: '0.75rem',
              color: '#374151'
            }}>
              Delete by date range or filters
            </div>
            <button
              onClick={() => alert('Advanced delete features coming soon!')}
              style={{
                width: '100%',
                marginTop: '8px',
                padding: '6px 12px',
                background: '#f3f4f6',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '0.7rem',
                cursor: 'pointer'
              }}
            >
              🛠️ Advanced Delete
            </button>
          </div> */}
        </div>

        {/* Warning Message */}
        <div style={{
          marginTop: '15px',
          padding: '12px',
          background: 'rgba(254, 226, 226, 0.5)',
          borderRadius: '8px',
          border: '1px solid #fecaca'
        }}>
          <div style={{
            fontSize: '0.8rem',
            color: '#dc2626',
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '4px'
          }}>
            ⚠️ Important
          </div>
          <div style={{
            fontSize: '0.75rem',
            color: '#7f1d1d'
          }}>
            Deleted data cannot be recovered. Please export your data before deleting.
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'white',
            padding: '30px',
            borderRadius: '15px',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.3)',
            maxWidth: '500px',
            width: '90%'
          }}>
            <h3 style={{
              margin: '0 0 15px 0',
              color: '#dc2626',
              fontSize: '1.3rem',
              fontWeight: '600'
            }}>
              🚨 Confirm Deletion
            </h3>
            
            <p style={{
              margin: '0 0 20px 0',
              color: '#374151',
              fontSize: '0.9rem',
              lineHeight: '1.5'
            }}>
              {deleteType === 'selected' 
                ? `You are about to delete ${selectedCount} selected record(s). This action cannot be undone.`
                : `You are about to delete ALL ${totalResults} records. This action cannot be undone.`
              }
            </p>

            <div style={{
              background: '#fef2f2',
              padding: '15px',
              borderRadius: '8px',
              border: '1px solid #fecaca',
              marginBottom: '20px'
            }}>
              <div style={{
                fontSize: '0.8rem',
                color: '#dc2626',
                fontWeight: '600',
                marginBottom: '5px'
              }}>
                ⚠️ Warning
              </div>
              <div style={{
                fontSize: '0.75rem',
                color: '#7f1d1d'
              }}>
                • This action is permanent and cannot be undone<br/>
                • All selected data will be permanently removed<br/>
                • Make sure you have exported any important data
              </div>
            </div>

            <div style={{
              display: 'flex',
              gap: '10px',
              justifyContent: 'flex-end'
            }}>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                disabled={deleting}
                style={{
                  padding: '10px 20px',
                  background: '#f3f4f6',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px',
                  color: '#374151',
                  fontSize: '0.9rem',
                  fontWeight: '600',
                  cursor: deleting ? 'not-allowed' : 'pointer',
                  opacity: deleting ? 0.6 : 1
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                disabled={deleting}
                style={{
                  padding: '10px 20px',
                  background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                  border: 'none',
                  borderRadius: '8px',
                  color: 'white',
                  fontSize: '0.9rem',
                  fontWeight: '600',
                  cursor: deleting ? 'not-allowed' : 'pointer',
                  opacity: deleting ? 0.6 : 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                {deleting ? (
                  <>
                    <div style={{ 
                      width: '16px', 
                      height: '16px', 
                      border: '2px solid white', 
                      borderTop: '2px solid transparent',
                      borderRadius: '50%', 
                      animation: 'spin 1s linear infinite' 
                    }} />
                    Deleting...
                  </>
                ) : (
                  <>
                    🗑️ Confirm Delete
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add CSS for spinner animation */}
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </>
  );
};

export default DeleteControls;