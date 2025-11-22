import React from "react"

const Switch = React.forwardRef(({ checked, onCheckedChange, className, ...props }, ref) => (
  <button
    ref={ref}
    role="switch"
    aria-checked={checked}
    onClick={() => onCheckedChange(!checked)}
    className={`peer inline-flex h-7 w-12 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent bg-gray-300 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${
      checked ? 'bg-blue-600' : 'bg-gray-300'
    } ${className}`}
    {...props}
  >
    <span
      className={`pointer-events-none block h-6 w-6 rounded-full bg-white shadow-lg ring-0 transition-transform ${
        checked ? 'translate-x-5' : 'translate-x-0'
      }`}
    />
  </button>
))
Switch.displayName = "Switch"

export { Switch }