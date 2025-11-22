import React from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Trash2, Calendar, Users, Plane } from "lucide-react";

export default function ResultsGrid({ calculations, onDelete }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      transition={{ duration: 0.5 }}
    >
      <Card className="border-none shadow-xl bg-white/80 backdrop-blur">
        <CardHeader className="border-b border-gray-100">
          <CardTitle className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-emerald-600" />
            Calculation History
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="space-y-4">
            {calculations.map((calc, index) => (
              <motion.div
                key={calc.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm hover:shadow-md transition-all duration-300"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-2">
                      <div className="flex items-center gap-2">
                        <Plane className="w-4 h-4 text-emerald-600" />
                        <span className="font-semibold text-gray-800">{calc.departure}</span>
                        <span className="text-gray-400">→</span>
                        <span className="font-semibold text-gray-800">{calc.destination}</span>
                      </div>
                      {calc.round_trip && (
                        <span className="bg-emerald-100 text-emerald-800 text-xs px-2 py-1 rounded-full">
                          Round Trip
                        </span>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Passengers:</span>
                        <div className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          <span className="font-medium">{calc.passengers}</span>
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-600">CO2 Emissions:</span>
                        <span className="font-medium text-amber-700">{calc.co2_kg} kg</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Distance:</span>
                        <span className="font-medium">{calc.distance_km} km</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Date:</span>
                        <span className="font-medium">
                          {new Date(calc.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onDelete(calc.id)}
                    className="text-red-600 border-red-200 hover:bg-red-50 hover:text-red-700 ml-4"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </motion.div>
            ))}
            
            {calculations.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                No calculations yet. Calculate your first flight emissions above!
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}