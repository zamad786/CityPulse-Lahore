import type { LucideIcon } from "lucide-react"

import { ArrowDownRight } from "lucide-react"


type KpiCardProps = {
  title: string
  value: string
  unit?: string
  subtitle: string
  icon: LucideIcon
  highlighted?: boolean
  pending?: boolean
}


export function KpiCard({
  title,
  value,
  unit,
  subtitle,
  icon: Icon,
  highlighted = false,
  pending = false,
}: KpiCardProps) {
  return (
    <div
      className={`
        relative overflow-hidden
        rounded-2xl p-5
        transition-all duration-200
        hover:-translate-y-0.5

        ${
          highlighted
            ? "citypulse-panel-strong citypulse-gold-glow"
            : "citypulse-panel"
        }
      `}
    >
      <div
        className="
          pointer-events-none
          absolute -right-10 -top-10
          size-32 rounded-full
          bg-primary/5 blur-3xl
        "
      />

      <div className="relative">
        <div className="flex items-start justify-between">
          <div>
            <div className="citypulse-eyebrow">
              {title}
            </div>

            <div className="mt-4 flex items-end gap-2">
              <span
                className={`
                  text-3xl font-semibold
                  tracking-[-0.04em]

                  ${
                    pending
                      ? "text-muted-foreground"
                      : highlighted
                        ? "citypulse-value"
                        : "text-white"
                  }
                `}
              >
                {value}
              </span>

              {unit && (
                <span className="mb-1 text-xs text-muted-foreground">
                  {unit}
                </span>
              )}
            </div>
          </div>

          <div className="citypulse-icon-box size-10">
            <Icon className="size-5" />
          </div>
        </div>

        <div className="mt-5 h-px bg-primary/10" />

        <div className="mt-3 flex items-center gap-2 text-[11px] text-muted-foreground">
          {!pending && (
            <ArrowDownRight className="size-3 text-primary" />
          )}

          {subtitle}
        </div>
      </div>
    </div>
  )
}