import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Cloud, MapPin, TreePine, Leaf, Download, Share2 } from "lucide-react";
import { motion } from "framer-motion";

export default function ResultsCard({ results, roundTrip, onNewCalculation }) {
  // Calculate tree equivalents (1 tree absorbs ~20kg CO2 per year)
  const treesNeeded = Math.ceil(results.co2_kg / 20);
  
  // Calculate car equivalent (average car emits ~4.6 tons CO2 per year)
  const carMonths = (results.co2_tonnes / 4.6 * 12).toFixed(1);

  const getEmissionLevel = (co2Kg) => {
    if (co2Kg < 100) return { level: "Low", color: "text-emerald-600", bg: "bg-emerald-100" };
    if (co2Kg < 500) return { level: "Moderate", color: "text-amber-600", bg: "bg-amber-100" };
    return { level: "High", color: "text-red-600", bg: "bg-red-100" };
  };

  const emissionLevel = getEmissionLevel(results.co2_kg);

  return (
    <motion.div
      key="results"
      initial={{ opacity: 0, x: 20, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 20, scale: 0.95 }}
      transition={{ duration: 0.5, type: "spring" }}
      className="h-full"
    >
      <Card className="border-0 shadow-2xl bg-gradient-to-br from-white via-white to-emerald-50/70 backdrop-blur-xl rounded-2xl overflow-hidden border border-white/20 h-full">
        {/* Animated Background Elements */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-200/30 rounded-full opacity-40 -mr-32 -mt-32 animate-pulse"></div>
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-teal-200/30 rounded-full opacity-40 -ml-24 -mb-24 animate-pulse delay-1000"></div>
        
        <CardHeader className="pb-4 border-b border-gray-100/50 bg-gradient-to-r from-white to-gray-50/80">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center shadow-lg">
                <Cloud className="w-6 h-6 text-white" />
              </div>
              <div>
                <CardTitle className="text-2xl font-bold text-gray-800">
                  Emission Results
                </CardTitle>
                <div className="flex items-center gap-2 mt-1">
                  <Badge className={`${emissionLevel.bg} ${emissionLevel.color} border-0 font-semibold`}>
                    {emissionLevel.level} Impact
                  </Badge>
                  <Badge className="bg-emerald-600 text-white px-3 py-1 border-0 font-semibold">
                    {roundTrip ? "Round Trip" : "One Way"}
                  </Badge>
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" className="rounded-lg border-gray-200">
                <Share2 className="w-4 h-4" />
              </Button>
              <Button variant="outline" size="sm" className="rounded-lg border-gray-200">
                <Download className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="pt-6 space-y-6 relative">
          {/* CO2 Emissions - Main Focus */}
          <motion.div 
            className="bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl p-6 text-white shadow-xl relative overflow-hidden"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
            <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/5 rounded-full -ml-12 -mb-12"></div>
            
            <div className="flex items-center gap-2 mb-4 opacity-90">
              <Cloud className="w-5 h-5" />
              <span className="text-sm font-semibold">Total CO2 Emissions</span>
            </div>
            
            <div className="grid grid-cols-2 gap-6 relative z-10">
              <div className="text-center">
                <div className="text-4xl font-bold mb-2 drop-shadow-sm">
                  {results.co2_kg.toLocaleString()}
                </div>
                <div className="text-emerald-100 font-semibold text-sm">KILOGRAMS</div>
              </div>
              
              <div className="text-center">
                <div className="text-4xl font-bold mb-2 drop-shadow-sm">
                  {results.co2_tonnes.toFixed(2)}
                </div>
                <div className="text-emerald-100 font-semibold text-sm">TONNES</div>
              </div>
            </div>
          </motion.div>

          {/* Distance & Route Info */}
          <motion.div 
            className="grid grid-cols-2 gap-4"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            <div className="bg-white rounded-xl p-4 border-2 border-gray-100 shadow-sm hover:shadow-md transition-all duration-300">
              <div className="flex items-center gap-2 text-gray-600 mb-3">
                <MapPin className="w-4 h-4 text-teal-600" />
                <span className="text-sm font-semibold">Distance</span>
              </div>
              <div className="text-2xl font-bold text-gray-800 mb-1">
                {results.distance_km.toLocaleString()}
              </div>
              <div className="text-gray-500 text-sm">kilometers</div>
            </div>

            <div className="bg-white rounded-xl p-4 border-2 border-gray-100 shadow-sm hover:shadow-md transition-all duration-300">
              <div className="flex items-center gap-2 text-gray-600 mb-3">
                <MapPin className="w-4 h-4 text-teal-600" />
                <span className="text-sm font-semibold">Distance</span>
              </div>
              <div className="text-2xl font-bold text-gray-800 mb-1">
                {results.distance_miles.toLocaleString()}
              </div>
              <div className="text-gray-500 text-sm">miles</div>
            </div>
          </motion.div>

          {/* Environmental Impact Context */}
          <motion.div 
            className="grid grid-cols-2 gap-4"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl p-4 border border-amber-200 shadow-sm">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 bg-amber-200 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
                  <TreePine className="w-5 h-5 text-amber-700" />
                </div>
                <div>
                  <h4 className="font-bold text-gray-800 mb-1 text-sm">Tree Equivalent</h4>
                  <p className="text-xs text-gray-700 leading-relaxed">
                    Equivalent to <strong className="text-amber-700">{treesNeeded} trees</strong> annual CO2 absorption
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-4 border border-blue-200 shadow-sm">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 bg-blue-200 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
                  <Leaf className="w-5 h-5 text-blue-700" />
                </div>
                <div>
                  <h4 className="font-bold text-gray-800 mb-1 text-sm">Car Equivalent</h4>
                  <p className="text-xs text-gray-700 leading-relaxed">
                    Like driving a car for <strong className="text-blue-700">{carMonths} months</strong>
                  </p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Flight Route Information */}
          {results.flight_info && (
            <motion.div 
              className="bg-gray-50/80 rounded-xl p-4 border border-gray-200/50 shadow-sm"
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.5 }}
            >
              <div className="flex items-center gap-2 text-gray-600 mb-2">
                <Leaf className="w-4 h-4 text-emerald-600" />
                <span className="text-sm font-semibold">Route Information</span>
              </div>
              <p className="text-gray-700 text-sm leading-relaxed font-medium">
                {results.flight_info}
              </p>
            </motion.div>
          )}

          {/* Additional Information */}
          <motion.div 
            className="pt-4 border-t border-gray-200/50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            <p className="text-xs text-gray-500 text-center leading-relaxed">
              📊 Calculations based on average economy class emissions (~90-115g CO2 per passenger-km)
              <br />
              🌱 Consider carbon offset programs to neutralize your flight's environmental impact
            </p>
          </motion.div>
        </CardContent>
      </Card>
    </motion.div>
  );
}