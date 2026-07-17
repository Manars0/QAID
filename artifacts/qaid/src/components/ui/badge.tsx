import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "../../lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        // Default uses the brand teal primary
        default:
          "border-transparent bg-primary text-primary-foreground",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground",
        destructive:
          "border-transparent bg-destructive text-white",
        outline:
          "text-foreground border-border",

        // Risk level badges — explicit brand colours matching new palette
        success:
          "border-transparent bg-[#10B981] text-white",          /* LOW   — #10B981 emerald  */
        warning:
          "border-transparent bg-[#F59E0B] text-white",          /* MEDIUM — #F59E0B amber    */
        danger:
          "border-transparent bg-[#F97316] text-white",          /* HIGH  — #F97316 orange   */
        critical:
          "border-transparent bg-[#EF4444] text-white",          /* CRIT  — #EF4444 red      */
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
