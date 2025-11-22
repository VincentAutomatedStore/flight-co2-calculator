import React from 'react';

const BatchParameterControls = ({ batchParams, setBatchParams, isProcessing }) => {
  const formatCabinClass = (cabin) => {
    return cabin.charAt(0).toUpperCase() + cabin.slice(1).replace('_', ' ');
  };

  return (
    <div style={{
      background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
      border: '2px solid #e2e8f0',
      borderRadius: '15px',
      padding: '20px',
      marginBottom: '25px'
    }}>
      <h3 style={{
        margin: '0 0 15px 0',
        color: '#1e40af',
        fontSize: '1.2rem',
        fontWeight: '600'
      }}>
        ⚙️ Batch Processing Parameters
      </h3>
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '20px',
        alignItems: 'end'
      }}>
        {/* Passengers Input */}
        <div>
          <label style={{
            display: 'block',
            marginBottom: '8px',
            fontWeight: '600',
            color: '#374151',
            fontSize: '0.9rem'
          }}>
            👥 Number of Passengers
          </label>
          <input
            type="number"
            min="1"
            max="999"
            value={batchParams.passengers}
            onChange={(e) => setBatchParams(prev => ({
              ...prev,
              passengers: parseInt(e.target.value) || 1
            }))}
            disabled={isProcessing}
            style={{
              width: '93%',
              padding: '10px 12px',
              border: '2px solid #d1d5db',
              borderRadius: '8px',
              fontSize: '1rem',
              background: 'white',
              transition: 'all 0.2s ease'
            }}
          />
        </div>

        {/* Cabin Class Selection */}
        <div>
          <label style={{
            display: 'block',
            marginBottom: '8px',
            fontWeight: '600',
            color: '#374151',
            fontSize: '0.9rem'
          }}>
            🛫 Cabin Class
          </label>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '8px'
          }}>
            {[
              { value: "economy", label: "Economy", multiplier: 1.0 },
              { value: "premium_economy", label: "Premium", multiplier: 1.3 },
              { value: "business", label: "Business", multiplier: 1.8 },
              { value: "first", label: "First", multiplier: 2.5 }
            ].map((cabin) => (
              <button
                key={cabin.value}
                type="button"
                onClick={() => setBatchParams(prev => ({
                  ...prev,
                  cabinClass: cabin.value
                }))}
                disabled={isProcessing}
                style={{
                  padding: '8px 6px',
                  border: `2px solid ${
                    batchParams.cabinClass === cabin.value ? '#3b82f6' : '#d1d5db'
                  }`,
                  borderRadius: '6px',
                  background: batchParams.cabinClass === cabin.value ? '#dbeafe' : 'white',
                  color: batchParams.cabinClass === cabin.value ? '#1e40af' : '#374151',
                  fontSize: '0.8rem',
                  fontWeight: '600',
                  cursor: isProcessing ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s ease',
                  opacity: isProcessing ? 0.6 : 1
                }}
              >
                {cabin.label}
                <div style={{
                  fontSize: '0.7rem',
                  color: batchParams.cabinClass === cabin.value ? '#3b82f6' : '#6b7280',
                  marginTop: '2px'
                }}>
                  {cabin.multiplier}x
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Round Trip Toggle */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '12px',
          background: 'white',
          borderRadius: '8px',
          border: '2px solid #d1d5db'
        }}>
          <div style={{ flex: 1 }}>
            <div style={{
              fontWeight: '600',
              color: '#374151',
              fontSize: '0.9rem',
              marginBottom: '2px'
            }}>
              🔄 Round Trip
            </div>
            <div style={{
              fontSize: '0.8rem',
              color: '#6b7280'
            }}>
              Include return journey
            </div>
          </div>
          <button
            onClick={() => setBatchParams(prev => ({
              ...prev,
              roundTrip: !prev.roundTrip
            }))}
            disabled={isProcessing}
            style={{
              width: '44px',
              height: '24px',
              background: batchParams.roundTrip ? '#10b981' : '#d1d5db',
              border: 'none',
              borderRadius: '12px',
              position: 'relative',
              cursor: isProcessing ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease',
              opacity: isProcessing ? 0.6 : 1
            }}
          >
            <div style={{
              width: '20px',
              height: '20px',
              background: 'white',
              borderRadius: '50%',
              position: 'absolute',
              top: '2px',
              left: batchParams.roundTrip ? '22px' : '2px',
              transition: 'all 0.2s ease',
              boxShadow: '0 1px 3px rgba(0,0,0,0.2)'
            }} />
          </button>
        </div>

        {/* Current Parameters Display */}
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
            📋 Current Settings
          </div>
          <div style={{
            fontSize: '0.75rem',
            color: '#374151'
          }}>
            {batchParams.passengers} passenger{batchParams.passengers !== 1 ? 's' : ''} • 
            {formatCabinClass(batchParams.cabinClass)} • 
            {batchParams.roundTrip ? 'Round Trip' : 'One Way'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BatchParameterControls;