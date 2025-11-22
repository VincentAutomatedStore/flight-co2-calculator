import React, { useState, useEffect } from 'react'
import { airports } from './data/airports'
import AutomationResults from './components/AutomationResults.jsx';
import AirportsList from './components/AirportsList.jsx';

function App() {
  const [departure, setDeparture] = useState('')
  const [destination, setDestination] = useState('')
  const [passengers, setPassengers] = useState(1)
  const [roundTrip, setRoundTrip] = useState(false)
  const [cabinClass, setCabinClass] = useState('economy')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [calculations, setCalculations] = useState([])
  const [activeTab, setActiveTab] = useState('calculator') // New state for active tab
  
  // New states for dropdowns
  const [showDepartureDropdown, setShowDepartureDropdown] = useState(false)
  const [showDestinationDropdown, setShowDestinationDropdown] = useState(false)
  const [departureSearch, setDepartureSearch] = useState('')
  const [destinationSearch, setDestinationSearch] = useState('')

  useEffect(() => {
    if (activeTab === 'history') {
      fetchCalculations()
    }
  }, [activeTab])

  const fetchCalculations = async () => {
    try {
      const response = await fetch('/api/results')
      if (response.ok) {
        const data = await response.json()
        setCalculations(data)
      }
    } catch (err) {
      console.error('Error fetching calculations:', err)
    }
  }

  const handleCalculate = async () => {
    if (!departure.trim() || !destination.trim()) {
      setError('Please enter both departure and destination')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await fetch('/api/calculate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          departure: departure.trim(),
          destination: destination.trim(),
          passengers: parseInt(passengers),
          round_trip: roundTrip,
          cabin_class: cabinClass
        })
      })

      const data = await response.json()

      if (data.success) {
        setResults(data.results)
        fetchCalculations()
        // Clear form after successful calculation
        clearForm()
      } else {
        setError(data.error || 'Calculation failed')
      }
    } catch (err) {
      setError('Network error. Please check if backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const clearForm = () => {
    setDeparture('')
    setDestination('')
    setPassengers(1)
    setRoundTrip(false)
    setCabinClass('economy')
    setDepartureSearch('')
    setDestinationSearch('')
    setShowDepartureDropdown(false)
    setShowDestinationDropdown(false)
  }

  const handleDeleteCalculation = async (id) => {
    try {
      const response = await fetch(`/api/delete/${id}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        setCalculations(calculations.filter(calc => calc.id !== id))
        if (results && results.id === id) {
          setResults(null)
        }
      }
    } catch (err) {
      console.error('Error deleting calculation:', err)
    }
  }

  const filteredDepartureAirports = airports.filter(airport =>
    airport.search.toLowerCase().includes(departureSearch.toLowerCase()) ||
    airport.code.toLowerCase().includes(departureSearch.toLowerCase())
  )

  const filteredDestinationAirports = airports.filter(airport =>
    airport.search.toLowerCase().includes(destinationSearch.toLowerCase()) ||
    airport.code.toLowerCase().includes(destinationSearch.toLowerCase())
  )

  const selectAirport = (type, airport) => {
    if (type === 'departure') {
      setDeparture(airport.code)
      setDepartureSearch(airport.search)
      setShowDepartureDropdown(false)
    } else {
      setDestination(airport.code)
      setDestinationSearch(airport.search)
      setShowDestinationDropdown(false)
    }
  }

  const cabinClasses = [
    { value: "economy", label: "Economy", color: "#2563eb" },
    { value: "premium_economy", label: "Premium Economy", color: "#059669" },
    { value: "business", label: "Business", color: "#7c3aed" },
    { value: "first", label: "First Class", color: "#d97706" }
  ]

  const formatCabinClass = (cabin) => {
    return cabin.charAt(0).toUpperCase() + cabin.slice(1).replace('_', ' ')
  }

  // Tab styles
  const tabStyles = {
    tabsContainer: {
      marginBottom: '40px'
    },
    tabsList: {
      display: 'flex',
      background: 'rgba(255, 255, 255, 0.9)',
      backdropFilter: 'blur(10px)',
      borderRadius: '15px',
      padding: '8px',
      boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)',
      border: '1px solid rgba(255, 255, 255, 0.3)',
      marginBottom: '30px'
    },
    tabTrigger: {
      flex: 1,
      padding: '15px 20px',
      borderRadius: '10px',
      border: 'none',
      background: 'transparent',
      fontSize: '1.1rem',
      fontWeight: '600',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      color: '#6b7280'
    },
    tabTriggerActive: {
      background: 'linear-gradient(135deg, #3b82f6 0%, #10b981 100%)',
      color: 'white',
      boxShadow: '0 5px 15px rgba(59, 130, 246, 0.4)'
    },
    tabContent: {
      // Content will be conditionally rendered
    }
  }

  // Comprehensive styling
  const styles = {
    // Layout
    container: {
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #dcfce7 100%)',
      padding: '20px',
      position: 'relative',
      overflow: 'hidden'
    },
    backgroundElements: {
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      overflow: 'hidden',
      pointerEvents: 'none',
      zIndex: 0
    },
    backgroundCircle1: {
      position: 'absolute',
      top: '-160px',
      right: '-160px',
      width: '320px',
      height: '320px',
      background: 'rgba(59, 130, 246, 0.1)',
      borderRadius: '50%',
      filter: 'blur(40px)'
    },
    backgroundCircle2: {
      position: 'absolute',
      bottom: '-160px',
      left: '-160px',
      width: '320px',
      height: '320px',
      background: 'rgba(16, 185, 129, 0.1)',
      borderRadius: '50%',
      filter: 'blur(40px)'
    },
    content: {
      position: 'relative',
      zIndex: 10,
      maxWidth: '1400px',
      margin: '0 auto'
    },

    // Header
    header: {
      textAlign: 'center',
      marginBottom: '40px'
    },
    headerContent: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '30px',
      marginBottom: '30px'
    },
    logoContainer: {
      position: 'relative'
    },
    mainLogo: {
      width: '100px',
      height: '100px',
      background: 'linear-gradient(135deg, #3b82f6 0%, #10b981 100%)',
      borderRadius: '25px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      boxShadow: '0 20px 40px rgba(59, 130, 246, 0.3)'
    },
    secondaryLogo: {
      position: 'absolute',
      bottom: '-10px',
      right: '-10px',
      width: '50px',
      height: '50px',
      background: '#f59e0b',
      borderRadius: '15px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      boxShadow: '0 10px 20px rgba(245, 158, 11, 0.3)'
    },
    title: {
      fontSize: '4rem',
      fontWeight: 'bold',
      background: 'linear-gradient(135deg, #1e40af 0%, #047857 100%)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      marginBottom: '15px'
    },
    subtitle: {
      fontSize: '1.5rem',
      color: '#6b7280',
      maxWidth: '800px',
      margin: '0 auto',
      lineHeight: '1.6'
    },

    // Grid Layout
    grid: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: '40px',
      alignItems: 'start',
      marginBottom: '60px'
    },

    // Cards
    card: {
      background: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(10px)',
      borderRadius: '25px',
      boxShadow: '0 25px 50px rgba(0, 0, 0, 0.15)',
      border: '1px solid rgba(255, 255, 255, 0.3)',
      overflow: 'hidden'
    },
    cardHeader: {
      background: 'linear-gradient(135deg, #3b82f6 0%, #10b981 100%)',
      padding: '30px',
      color: 'white'
    },
    cardHeaderContent: {
      display: 'flex',
      alignItems: 'center',
      gap: '20px'
    },
    cardIcon: {
      width: '60px',
      height: '60px',
      background: 'rgba(255, 255, 255, 0.2)',
      borderRadius: '15px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    },
    cardTitle: {
      fontSize: '2rem',
      fontWeight: 'bold',
      marginBottom: '5px'
    },
    cardSubtitle: {
      color: 'rgba(255, 255, 255, 0.9)',
      fontSize: '1.1rem'
    },
    cardBody: {
      padding: '30px'
    },

    // Form Elements
    formGroup: {
      marginBottom: '25px',
      position: 'relative'
    },
    label: {
      display: 'flex',
      alignItems: 'center',
      gap: '15px',
      fontSize: '1.2rem',
      fontWeight: '600',
      color: '#374151',
      marginBottom: '12px'
    },
    labelIcon: {
      width: '50px',
      height: '50px',
      background: '#dbeafe',
      borderRadius: '12px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    },
    input: {
      width: '100%',
      height: '60px',
      padding: '0 20px',
      border: '2px solid #e5e7eb',
      borderRadius: '15px',
      fontSize: '1.1rem',
      transition: 'all 0.3s ease',
      boxSizing: 'border-box'
    },
    dropdown: {
      position: 'absolute',
      top: '100%',
      left: 0,
      right: 0,
      background: 'white',
      border: '2px solid #e5e7eb',
      borderTop: 'none',
      borderRadius: '0 0 15px 15px',
      maxHeight: '200px',
      overflowY: 'auto',
      zIndex: 1000,
      boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)'
    },
    dropdownItem: {
      padding: '15px 20px',
      borderBottom: '1px solid #f3f4f6',
      cursor: 'pointer',
      transition: 'background 0.2s ease'
    },
    dropdownItemHover: {
      background: '#f3f4f6'
    },
    airportCode: {
      fontWeight: 'bold',
      color: '#3b82f6',
      marginRight: '10px'
    },
    airportName: {
      color: '#6b7280',
      fontSize: '0.9rem'
    },
    hint: {
      fontSize: '0.9rem',
      color: '#6b7280',
      marginTop: '8px',
      display: 'flex',
      alignItems: 'center',
      gap: '5px'
    },

    // Cabin Class Buttons
    cabinGrid: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: '15px'
    },
    cabinButton: {
      padding: '20px',
      borderRadius: '15px',
      border: '2px solid',
      textAlign: 'center',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      background: 'white'
    },
    cabinButtonActive: {
      fontWeight: '600',
      transform: 'translateY(-2px)',
      boxShadow: '0 10px 20px rgba(0, 0, 0, 0.1)'
    },
    cabinLabel: {
      fontSize: '1rem',
      fontWeight: '600',
      marginBottom: '5px'
    },
    cabinMultiplier: {
      fontSize: '0.8rem',
      opacity: 0.8
    },

    // Round Trip Toggle
    roundTripContainer: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '25px',
      background: 'linear-gradient(135deg, #dbeafe 0%, #d1fae5 100%)',
      borderRadius: '20px',
      border: '2px solid #bfdbfe'
    },
    roundTripContent: {
      display: 'flex',
      alignItems: 'center',
      gap: '20px'
    },
    roundTripIcon: {
      width: '70px',
      height: '70px',
      background: 'white',
      borderRadius: '15px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      boxShadow: '0 5px 15px rgba(0, 0, 0, 0.1)',
      border: '1px solid #bfdbfe'
    },
    roundTripLabel: {
      fontSize: '1.3rem',
      fontWeight: '600',
      color: '#1f2937'
    },
    roundTripDescription: {
      fontSize: '0.9rem',
      color: '#6b7280',
      marginTop: '5px'
    },
    toggle: {
      width: '70px',
      height: '35px',
      background: '#d1d5db',
      borderRadius: '50px',
      position: 'relative',
      cursor: 'pointer',
      transition: 'all 0.3s ease'
    },
    toggleActive: {
      background: '#3b82f6'
    },
    toggleKnob: {
      position: 'absolute',
      top: '3px',
      left: '3px',
      width: '29px',
      height: '29px',
      background: 'white',
      borderRadius: '50%',
      transition: 'all 0.3s ease',
      boxShadow: '0 2px 5px rgba(0, 0, 0, 0.2)'
    },
    toggleKnobActive: {
      left: '38px'
    },

    // Error Alert
    errorAlert: {
      background: '#fef2f2',
      border: '1px solid #fecaca',
      color: '#dc2626',
      padding: '20px',
      borderRadius: '15px',
      display: 'flex',
      alignItems: 'center',
      gap: '12px'
    },

    // Calculate Button
    calculateButton: {
      width: '100%',
      height: '70px',
      background: 'linear-gradient(135deg, #3b82f6 0%, #10b981 100%)',
      color: 'white',
      border: 'none',
      borderRadius: '15px',
      fontSize: '1.3rem',
      fontWeight: 'bold',
      cursor: 'pointer',
      boxShadow: '0 15px 30px rgba(59, 130, 246, 0.4)',
      transition: 'all 0.3s ease',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '12px'
    },
    calculateButtonHover: {
      transform: 'translateY(-3px)',
      boxShadow: '0 20px 40px rgba(59, 130, 246, 0.6)'
    },
    calculateButtonDisabled: {
      opacity: 0.6,
      cursor: 'not-allowed',
      transform: 'none'
    },
    spinner: {
      width: '24px',
      height: '24px',
      border: '3px solid rgba(255, 255, 255, 0.3)',
      borderTop: '3px solid white',
      borderRadius: '50%',
      animation: 'spin 1s linear infinite'
    },

    // Results
    resultsHeader: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      marginBottom: '10px'
    },
    badges: {
      display: 'flex',
      flexWrap: 'wrap',
      gap: '10px',
      marginTop: '15px'
    },
    badge: {
      background: 'rgba(255, 255, 255, 0.2)',
      padding: '8px 16px',
      borderRadius: '50px',
      fontSize: '0.9rem',
      fontWeight: '500'
    },
    dataSource: {
      background: 'rgba(255, 255, 255, 0.2)',
      padding: '6px 12px',
      borderRadius: '8px',
      fontSize: '0.8rem'
    },
    resultItem: {
      background: '#f8fafc',
      padding: '30px',
      borderRadius: '20px',
      marginBottom: '20px',
      textAlign: 'center',
      border: '1px solid #e2e8f0',
      boxShadow: '0 5px 15px rgba(0, 0, 0, 0.05)'
    },
    resultValue: {
      fontSize: '3rem',
      fontWeight: 'bold',
      marginBottom: '10px'
    },
    resultLabel: {
      fontSize: '1.1rem',
      fontWeight: '600'
    },
    distanceGrid: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: '15px'
    },
    distanceItem: {
      background: '#f8fafc',
      padding: '25px',
      borderRadius: '15px',
      textAlign: 'center',
      border: '1px solid #e2e8f0'
    },
    distanceValue: {
      fontSize: '1.8rem',
      fontWeight: 'bold',
      color: '#374151',
      marginBottom: '8px'
    },
    environmentalImpact: {
      background: 'linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%)',
      border: '1px solid #bbf7d0',
      padding: '25px',
      borderRadius: '15px',
      marginTop: '20px'
    },

    // Empty State
    emptyState: {
      background: 'rgba(255, 255, 255, 0.8)',
      padding: '60px 40px',
      borderRadius: '25px',
      textAlign: 'center',
      border: '2px dashed #d1d5db'
    },
    emptyIcon: {
      fontSize: '5rem',
      marginBottom: '20px'
    },

    // History
    history: {
      background: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(10px)',
      borderRadius: '25px',
      padding: '40px',
      boxShadow: '0 25px 50px rgba(0, 0, 0, 0.15)',
      border: '1px solid rgba(255, 255, 255, 0.3)'
    },
    historyTitle: {
      fontSize: '2rem',
      fontWeight: 'bold',
      color: '#1f2937',
      textAlign: 'center',
      marginBottom: '30px'
    },
    historyItem: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '25px',
      background: '#f8fafc',
      borderRadius: '15px',
      marginBottom: '15px',
      border: '1px solid #e2e8f0',
      transition: 'all 0.3s ease'
    },
    historyItemHover: {
      background: '#f1f5f9',
      transform: 'translateY(-2px)',
      boxShadow: '0 5px 15px rgba(0, 0, 0, 0.1)'
    },
    historyLeft: {
      display: 'flex',
      alignItems: 'center',
      gap: '20px',
      flex: 1
    },
    historyIcon: {
      width: '60px',
      height: '60px',
      background: 'linear-gradient(135deg, #3b82f6 0%, #10b981 100%)',
      borderRadius: '12px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'white',
      fontSize: '1.5rem'
    },
    historyRoute: {
      fontSize: '1.1rem',
      fontWeight: '600',
      color: '#1f2937'
    },
    historyDetails: {
      fontSize: '0.9rem',
      color: '#6b7280',
      marginTop: '5px'
    },
    historyRight: {
      textAlign: 'right',
      display: 'flex',
      alignItems: 'center',
      gap: '15px'
    },
    historyCO2: {
      fontSize: '1.3rem',
      fontWeight: 'bold',
      color: '#3b82f6'
    },
    historyFuel: {
      fontSize: '0.9rem',
      color: '#6b7280',
      marginTop: '5px'
    },
    deleteButton: {
      background: '#ef4444',
      color: 'white',
      border: 'none',
      borderRadius: '8px',
      padding: '8px 16px',
      cursor: 'pointer',
      fontSize: '0.9rem',
      fontWeight: '600',
      transition: 'all 0.2s ease'
    },
    deleteButtonHover: {
      background: '#dc2626',
      transform: 'scale(1.05)'
    }
  }

  // Add CSS animation for spinner
  const spinnerStyle = `
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `

  // Render calculator content
  const renderCalculatorContent = () => (
    <div style={styles.grid}>
      {/* Input Card */}
      <div>
        <div style={styles.card}>
          <div style={styles.cardHeader}>
            <div style={styles.cardHeaderContent}>
              <div style={styles.cardIcon}>
                <span style={{ fontSize: '2rem' }}>✈️</span>
              </div>
              <div>
                <h2 style={styles.cardTitle}>Flight Details</h2>
                <p style={styles.cardSubtitle}>Enter your journey information</p>
              </div>
            </div>
          </div>
          
          <div style={styles.cardBody}>
            {/* Departure Airport Dropdown */}
            <div style={styles.formGroup}>
              <div style={styles.label}>
                <div style={styles.labelIcon}>
                  <span style={{ fontSize: '1.5rem', color: '#3b82f6' }}>📍</span>
                </div>
                <span>Departure Airport</span>
              </div>
              <input
                type="text"
                placeholder="Search by airport code or name..."
                value={departureSearch}
                onChange={(e) => {
                  setDepartureSearch(e.target.value)
                  setShowDepartureDropdown(true)
                  if (!e.target.value) {
                    setDeparture('')
                  }
                }}
                onFocus={() => setShowDepartureDropdown(true)}
                style={styles.input}
                disabled={loading}
              />
              {showDepartureDropdown && filteredDepartureAirports.length > 0 && (
                <div style={styles.dropdown}>
                  {filteredDepartureAirports.map((airport) => (
                    <div
                      key={airport.code}
                      style={styles.dropdownItem}
                      onClick={() => selectAirport('departure', airport)}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = styles.dropdownItemHover.background
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'white'
                      }}
                    >
                      <div>
                        <span style={styles.airportCode}>({airport.code})</span>
                        {airport.search}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <div style={styles.hint}>
                <span>💡</span> Search by airport code (AAL) or name
              </div>
            </div>

            {/* Destination Airport Dropdown */}
            <div style={styles.formGroup}>
              <div style={styles.label}>
                <div style={{...styles.labelIcon, background: '#d1fae5'}}>
                  <span style={{ fontSize: '1.5rem', color: '#10b981' }}>🎯</span>
                </div>
                <span>Destination Airport</span>
              </div>
              <input
                type="text"
                placeholder="Search by airport code or name..."
                value={destinationSearch}
                onChange={(e) => {
                  setDestinationSearch(e.target.value)
                  setShowDestinationDropdown(true)
                  if (!e.target.value) {
                    setDestination('')
                  }
                }}
                onFocus={() => setShowDestinationDropdown(true)}
                style={styles.input}
                disabled={loading}
              />
              {showDestinationDropdown && filteredDestinationAirports.length > 0 && (
                <div style={styles.dropdown}>
                  {filteredDestinationAirports.map((airport) => (
                    <div
                      key={airport.code}
                      style={styles.dropdownItem}
                      onClick={() => selectAirport('destination', airport)}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = styles.dropdownItemHover.background
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'white'
                      }}
                    >
                      <div>
                        <span style={styles.airportCode}>({airport.code})</span>
                        {airport.search}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <div style={styles.hint}>
                <span>💡</span> Search by airport code (CPH) or name
              </div>
            </div>

            {/* Passengers */}
            <div style={styles.formGroup}>
              <div style={styles.label}>
                <div style={{...styles.labelIcon, background: '#f3e8ff'}}>
                  <span style={{ fontSize: '1.5rem', color: '#8b5cf6' }}>👥</span>
                </div>
                <span>Number of Passengers</span>
              </div>
              <input
                type="number"
                min="1"
                max="999"
                value={passengers}
                onChange={(e) => setPassengers(parseInt(e.target.value) || 1)}
                style={styles.input}
                disabled={loading}
              />
            </div>

            {/* Cabin Class */}
            <div style={styles.formGroup}>
              <div style={styles.label}>
                <div style={{...styles.labelIcon, background: '#fef3c7'}}>
                  <span style={{ fontSize: '1.5rem', color: '#f59e0b' }}>💺</span>
                </div>
                <span>Cabin Class</span>
              </div>
              <div style={styles.cabinGrid}>
                {cabinClasses.map((cabin) => (
                  <button
                    key={cabin.value}
                    type="button"
                    onClick={() => setCabinClass(cabin.value)}
                    style={{
                      ...styles.cabinButton,
                      borderColor: cabinClass === cabin.value ? cabin.color : '#d1d5db',
                      background: cabinClass === cabin.value ? `${cabin.color}15` : 'white',
                      color: cabinClass === cabin.value ? cabin.color : '#374151',
                      fontWeight: cabinClass === cabin.value ? '600' : '400',
                      ...(cabinClass === cabin.value && styles.cabinButtonActive)
                    }}
                    disabled={loading}
                  >
                    <div style={styles.cabinLabel}>{cabin.label}</div>
                    <div style={styles.cabinMultiplier}>
                      {cabin.value === 'economy' ? '1.0x emissions' : 
                       cabin.value === 'premium_economy' ? '1.3x emissions' :
                       cabin.value === 'business' ? '1.8x emissions' : '2.5x emissions'}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Round Trip Toggle */}
            <div style={styles.formGroup}>
              <div style={styles.roundTripContainer}>
                <div style={styles.roundTripContent}>
                  <div style={styles.roundTripIcon}>
                    <span style={{ fontSize: '2rem', color: '#3b82f6' }}>🔄</span>
                  </div>
                  <div>
                    <div style={styles.roundTripLabel}>Round Trip Flight</div>
                    <div style={styles.roundTripDescription}>Include return journey in calculation</div>
                  </div>
                </div>
                <div 
                  style={{
                    ...styles.toggle,
                    ...(roundTrip && styles.toggleActive)
                  }}
                  onClick={() => setRoundTrip(!roundTrip)}
                >
                  <div style={{
                    ...styles.toggleKnob,
                    ...(roundTrip && styles.toggleKnobActive)
                  }} />
                </div>
              </div>
            </div>

            {/* Error Alert */}
            {error && (
              <div style={styles.formGroup}>
                <div style={styles.errorAlert}>
                  <span style={{ fontSize: '1.2rem' }}>⚠️</span>
                  <span style={{ fontWeight: '600' }}>{error}</span>
                </div>
              </div>
            )}

            {/* Calculate Button */}
            <div style={styles.formGroup}>
              <button
                onClick={handleCalculate}
                disabled={loading || !departure.trim() || !destination.trim()}
                style={{
                  ...styles.calculateButton,
                  ...((!loading && departure.trim() && destination.trim()) && styles.calculateButtonHover),
                  ...((loading || !departure.trim() || !destination.trim()) && styles.calculateButtonDisabled)
                }}
              >
                {loading ? (
                  <>
                    <div style={styles.spinner}></div>
                    Calculating Emissions...
                  </>
                ) : (
                  <>
                    <span style={{ fontSize: '1.5rem' }}>🧮</span>
                    Calculate CO₂ Emissions
                  </>
                )}
              </button>
            </div>

            {/* Quick Tips */}
            <div style={{ paddingTop: '20px', borderTop: '1px solid #e5e7eb' }}>
              <div style={styles.hint}>
                <span>💡</span> 
                <strong> Try:</strong> AAL → CPH • JFK → LHR • LAX → NRT
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Results Area */}
      <div>
        {results ? (
          <div style={styles.card}>
            <div style={styles.cardHeader}>
              <div style={styles.resultsHeader}>
                <div>
                  <h2 style={styles.cardTitle}>Emission Results</h2>
                  <div style={styles.badges}>
                    <div style={styles.badge}>
                      {roundTrip ? "Round Trip" : "One Way"}
                    </div>
                    <div style={styles.badge}>
                      {passengers} Passenger{passengers > 1 ? 's' : ''}
                    </div>
                    <div style={styles.badge}>
                      {formatCabinClass(cabinClass)}
                    </div>
                  </div>
                </div>
                <div style={styles.dataSource}>
                  ICAO Methodology
                </div>
              </div>
            </div>
            
            <div style={styles.cardBody}>
              {/* Fuel Burn */}
              <div style={{...styles.resultItem, background: '#fffbeb', borderColor: '#fed7aa'}}>
                <div style={{...styles.resultValue, color: '#ea580c'}}>
                  {results.fuel_burn_kg?.toLocaleString()} KG
                </div>
                <div style={{...styles.resultLabel, color: '#ea580c'}}>
                  Passenger Fuel Allocation
                </div>
              </div>

              {/* CO2 Emissions */}
              <div style={{...styles.resultItem, background: '#fef2f2', borderColor: '#fecaca'}}>
                <div style={{...styles.resultValue, color: '#dc2626'}}>
                  {results.total_co2_kg?.toLocaleString()} KG
                </div>
                <div style={{...styles.resultLabel, color: '#dc2626'}}>
                  Total Passengers' CO₂
                </div>
              </div>

              {/* Per Passenger CO2 */}
              <div style={{...styles.resultItem, background: '#eff6ff', borderColor: '#bfdbfe'}}>
                <div style={{...styles.resultValue, color: '#2563eb'}}>
                  {results.co2_per_passenger_kg?.toLocaleString()} KG
                </div>
                <div style={{...styles.resultLabel, color: '#2563eb'}}>
                  CO₂ per Passenger
                </div>
              </div>

              {/* Distance */}
              <div style={styles.distanceGrid}>
                <div style={styles.distanceItem}>
                  <div style={styles.distanceValue}>
                    {results.distance_km?.toLocaleString()}
                  </div>
                  <div style={{ color: '#6b7280' }}>Kilometers</div>
                </div>
                <div style={styles.distanceItem}>
                  <div style={styles.distanceValue}>
                    {results.distance_miles?.toLocaleString()}
                  </div>
                  <div style={{ color: '#6b7280' }}>Miles</div>
                </div>
              </div>

              {/* Environmental Impact */}
              <div style={styles.environmentalImpact}>
                <div style={{...styles.label, marginBottom: '15px'}}>
                  <span style={{ fontSize: '1.2rem' }}>🌳</span>
                  <span style={{ fontSize: '1.1rem', fontWeight: '600', color: '#065f46' }}>
                    Environmental Impact
                  </span>
                </div>
                <p style={{ color: '#065f46', margin: 0, lineHeight: '1.5' }}>
                  This flight's emissions equal the annual CO₂ absorption of 
                  <strong style={{ color: '#059669' }}> {Math.ceil(results.total_co2_kg / 20)} trees</strong>
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div style={styles.emptyState}>
            <div style={styles.emptyIcon}>🧮</div>
            <h3 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#6b7280', marginBottom: '10px' }}>
              Ready to Calculate
            </h3>
            <p style={{ color: '#9ca3af', fontSize: '1.1rem' }}>
              Enter your flight details to see the environmental impact calculation using ICAO methodology
            </p>
          </div>
        )}
      </div>
    </div>
  )

  // Render history content
  const renderHistoryContent = () => (
    calculations.length > 0 ? (
      <div style={styles.history}>
        <h2 style={styles.historyTitle}>Calculation History</h2>
        <div>
          {calculations.slice(0, 5).map((calc) => (
            <div 
              key={calc.id} 
              style={styles.historyItem}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = styles.historyItemHover.background;
                e.currentTarget.style.transform = styles.historyItemHover.transform;
                e.currentTarget.style.boxShadow = styles.historyItemHover.boxShadow;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = styles.historyItem.background;
                e.currentTarget.style.transform = 'none';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <div style={styles.historyLeft}>
                <div style={styles.historyIcon}>✈️</div>
                <div>
                  <div style={styles.historyRoute}>
                    {calc.departure} → {calc.destination}
                  </div>
                  <div style={styles.historyDetails}>
                    {calc.passengers} passenger{calc.passengers > 1 ? 's' : ''} • 
                    {calc.round_trip ? ' Round Trip' : ' One Way'} • 
                    {formatCabinClass(calc.cabin_class)}
                  </div>
                </div>
              </div>
              <div style={styles.historyRight}>
                <div>
                  <div style={styles.historyCO2}>
                    {calc.total_co2_kg} kg CO₂
                  </div>
                  <div style={styles.historyFuel}>
                    {calc.fuel_burn_kg} kg fuel
                  </div>
                </div>
                <button
                  onClick={() => handleDeleteCalculation(calc.id)}
                  style={styles.deleteButton}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = styles.deleteButtonHover.background;
                    e.currentTarget.style.transform = styles.deleteButtonHover.transform;
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = styles.deleteButton.background;
                    e.currentTarget.style.transform = 'none';
                  }}
                  title="Delete this calculation"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    ) : (
      <div style={styles.emptyState}>
        <div style={styles.emptyIcon}>📊</div>
        <h3 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#6b7280', marginBottom: '10px' }}>
          No Calculation History
        </h3>
        <p style={{ color: '#9ca3af', fontSize: '1.1rem' }}>
          Your previous calculations will appear here. Start by calculating a flight!
        </p>
      </div>
    )
  )

  // Render automation content
  const renderAutomationContent = () => (
    <AutomationResults />
  )

return (
  <>
    <style>{spinnerStyle}</style>
    <div style={styles.container}>
      {/* Background Elements */}
      <div style={styles.backgroundElements}>
        <div style={styles.backgroundCircle1}></div>
        <div style={styles.backgroundCircle2}></div>
      </div>

      <div style={styles.content}>
        {/* Header */}
        <div style={styles.header}>
          <div style={styles.headerContent}>
            <div style={styles.logoContainer}>
              <div style={styles.mainLogo}>
                <span style={{ fontSize: '2.5rem', color: 'white' }}>✈️</span>
              </div>
              <div style={styles.secondaryLogo}>
                <span style={{ fontSize: '1.5rem', color: 'white' }}>🌱</span>
              </div>
            </div>
            <div>
              <h1 style={styles.title}>Flight CO₂ Calculator</h1>
              <p style={styles.subtitle}>
                Calculate your flight's carbon footprint using official ICAO methodology and emission factors
              </p>
            </div>
          </div>
        </div>

        {/* Tabs Navigation - UPDATED SECTION */}
        <div style={tabStyles.tabsContainer}>
          <div style={tabStyles.tabsList}>
            <button
              style={{
                ...tabStyles.tabTrigger,
                ...(activeTab === 'calculator' && tabStyles.tabTriggerActive)
              }}
              onClick={() => setActiveTab('calculator')}
            >
              Single Calculation
            </button>
            <button
              style={{
                ...tabStyles.tabTrigger,
                ...(activeTab === 'history' && tabStyles.tabTriggerActive)
              }}
              onClick={() => setActiveTab('history')}
            >
              Calculation History
            </button>
            <button
              style={{
                ...tabStyles.tabTrigger,
                ...(activeTab === 'automation' && tabStyles.tabTriggerActive)
              }}
              onClick={() => setActiveTab('automation')}
            >
              Batch Processing
            </button>
            {/* Add the new Airports tab */}
            <button
              style={{
                ...tabStyles.tabTrigger,
                ...(activeTab === 'airports' && tabStyles.tabTriggerActive)
              }}
              onClick={() => setActiveTab('airports')}
            >
              Airports Database
            </button>
          </div>

          {/* Tab Content */}
          <div style={tabStyles.tabContent}>
            {activeTab === 'calculator' && renderCalculatorContent()}
            {activeTab === 'history' && renderHistoryContent()}
            {activeTab === 'automation' && renderAutomationContent()}
            {activeTab === 'airports' && <AirportsList />}
          </div>
        </div>
      </div>
    </div>
  </>
)}

export default App