import React from "react"

const Alert = React.forwardRef(({ className, variant = "default", ...props }, ref) => {
  const variants = {
    default: "bg-white text-gray-900",
    destructive: "border-red-200 bg-red-50 text-red-800",
  }
  
  return (
    <div
      ref={ref}
      role="alert"
      className={`relative w-full rounded-lg border border-gray-200 p-4 ${variants[variant]} ${className}`}
      {...props}
    />
  )
})
Alert.displayName = "Alert"

const AlertDescription = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={`text-sm ${className}`}
    {...props}
  />
))
AlertDescription.displayName = "AlertDescription"

export { Alert, AlertDescription }