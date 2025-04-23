import React from "react";

export function Button({ children, className, variant = "default", ...props }) {
  const getVariantClasses = () => {
    switch (variant) {
      case "outline":
        return "border border-input bg-background hover:bg-accent hover:text-accent-foreground";
      case "secondary":
        return "bg-secondary text-secondary-foreground hover:bg-secondary/80";
      case "ghost":
        return "hover:bg-accent hover:text-accent-foreground";
      case "link":
        return "text-primary underline-offset-4 hover:underline";
      default:
        return "bg-primary text-primary-foreground hover:bg-primary/90";
    }
  };

  return (
    <button
      className={`inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${getVariantClasses()} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
