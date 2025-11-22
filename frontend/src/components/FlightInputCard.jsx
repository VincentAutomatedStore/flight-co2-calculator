import React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "./ui/card";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Button } from "./ui/button";
import { Switch } from "./ui/switch";
import { Alert, AlertDescription } from "./ui/alert";
import { MapPin, Plane, Users, Calculator, AlertCircle } from "lucide-react";

export default function FlightInputCard({
  departure,
  setDeparture,
  destination,
  setDestination,
  passengers,
  setPassengers,
  roundTrip,
  setRoundTrip,
  onCalculate,
  loading,
  error
}) {
  return (
    <Card className="w-full border border-gray-200 shadow-2xl bg-white">
      <CardHeader className="text-center pb-6">
        <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
          <Plane className="w-8 h-8 text-white" />
        </div>
        <CardTitle className="text-3xl font-bold text-gray-800">
          Flight Details
        </CardTitle>
        <CardDescription className="text-lg text-gray-600">
          Enter your journey information
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Cabin Class */}
        <div className="space-y-3">
          <Label className="text-base font-semibold text-gray-700 flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center">
              <User className="w-5 h-5 text-amber-600" />
            </div>
            <span>Cabin Class</span>
          </Label>
          <div className="grid grid-cols-2 gap-3">
            {[
              { value: "economy", label: "Economy", multiplier: 1.0 },
              { value: "premium_economy", label: "Premium Economy", multiplier: 1.3 },
              { value: "business", label: "Business", multiplier: 1.8 },
              { value: "first", label: "First Class", multiplier: 2.5 }
            ].map((cabin) => (
              <button
                key={cabin.value}
                type="button"
                onClick={() => setCabinClass(cabin.value)}
                className={`p-3 rounded-xl border-2 text-center transition-all ${
                  cabinClass === cabin.value
                    ? 'border-blue-500 bg-blue-50 text-blue-700 font-semibold'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                }`}
                disabled={loading}
              >
                <div className="text-sm font-medium">{cabin.label}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {cabin.multiplier}x emissions
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Departure */}
        <div className="space-y-3">
          <Label htmlFor="departure" className="text-base font-semibold text-gray-700 flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
              <MapPin className="w-5 h-5 text-blue-600" />
            </div>
            <span>Departure Airport</span>
          </Label>
          <Input
            id="departure"
            placeholder="e.g., New York JFK or LHR"
            value={departure}
            onChange={(e) => setDeparture(e.target.value)}
            disabled={loading}
          />
          <p className="text-sm text-gray-500">
            Enter city name or airport code
          </p>
        </div>

        {/* Destination */}
        <div className="space-y-3">
          <Label htmlFor="destination" className="text-base font-semibold text-gray-700 flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
              <MapPin className="w-5 h-5 text-green-600" />
            </div>
            <span>Destination Airport</span>
          </Label>
          <Input
            id="destination"
            placeholder="e.g., London Heathrow or CDG"
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            disabled={loading}
          />
          <p className="text-sm text-gray-500">
            Enter city name or airport code
          </p>
        </div>

        {/* Passengers */}
        <div className="space-y-3">
          <Label htmlFor="passengers" className="text-base font-semibold text-gray-700 flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
              <Users className="w-5 h-5 text-purple-600" />
            </div>
            <span>Number of Passengers</span>
          </Label>
          <Input
            id="passengers"
            type="number"
            min="1"
            max="999"
            value={passengers}
            onChange={(e) => setPassengers(parseInt(e.target.value) || 1)}
            disabled={loading}
          />
        </div>

        {/* Round Trip Toggle */}
        <div className="flex items-center justify-between p-5 bg-blue-50 rounded-2xl border border-blue-200">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center shadow-sm border border-blue-200">
              <Plane className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <Label htmlFor="roundtrip" className="text-lg font-semibold text-gray-800 cursor-pointer">
                Round Trip Flight
              </Label>
              <p className="text-sm text-gray-600">Include return journey in calculation</p>
            </div>
          </div>
          <Switch
            id="roundtrip"
            checked={roundTrip}
            onCheckedChange={setRoundTrip}
            disabled={loading}
          />
        </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" className="rounded-xl">
            <AlertCircle className="h-5 w-5" />
            <AlertDescription className="font-medium">{error}</AlertDescription>
          </Alert>
        )}

        {/* Calculate Button */}
        <Button
          onClick={onCalculate}
          disabled={loading || !departure.trim() || !destination.trim()}
          size="lg"
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold shadow-lg hover:shadow-xl transition-all duration-300 mt-4"
        >
          {loading ? (
            <>
              <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin mr-3" />
              Calculating Emissions...
            </>
          ) : (
            <>
              <Calculator className="w-6 h-6 mr-3" />
              Calculate CO2 Emissions
            </>
          )}
        </Button>

        {/* Quick Tips */}
        <div className="pt-4 border-t border-gray-200">
          <p className="text-sm text-gray-500 text-center">
            💡 <strong>Try:</strong> JFK → LHR • LAX → NRT • CDG → DXB
          </p>
        </div>
      </CardContent>
    </Card>
  );
}