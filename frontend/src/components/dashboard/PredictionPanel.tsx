import {
  Activity,
  ArrowRight,
  BrainCircuit,
  MapPin,
  ShieldAlert,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"


type PredictionPanelProps = {
  currentPm25: number
  predictedPm25: number
  riskLevel: string
}


export function PredictionPanel({
  currentPm25,
  predictedPm25,
  riskLevel,
}: PredictionPanelProps) {
  const difference =
    predictedPm25 - currentPm25

  const percentChange =
    currentPm25 === 0
      ? 0
      : (difference / currentPm25) * 100

  return (
    <section
      className="
        relative overflow-hidden
        rounded-2xl p-6
        citypulse-panel-strong
      "
    >
      <div
        className="
          pointer-events-none
          absolute -right-20 -top-20
          size-72 rounded-full
          bg-primary/7 blur-3xl
        "
      />

      <div className="relative">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <BrainCircuit className="size-4 text-primary" />

              <span className="citypulse-eyebrow">
                AI Prediction Intelligence
              </span>
            </div>

            <h2 className="mt-2 text-xl font-semibold text-white">
              PM2.5 Forecast
            </h2>

            <p className="mt-1 text-xs text-muted-foreground">
              Historical validated test sample · 1-hour forecast
            </p>
          </div>

          <Badge
            variant="outline"
            className="
              border-primary/30
              bg-primary/10
              px-3 py-1.5
              text-primary
            "
          >
            <ShieldAlert className="mr-1.5 size-3.5" />
            {riskLevel}
          </Badge>
        </div>

        <div className="my-6 citypulse-gold-line" />

        <div
          className="
            grid gap-4
            md:grid-cols-[1fr_auto_1fr]
            md:items-center
          "
        >
          <div
            className="
              rounded-xl
              border border-primary/15
              bg-black/10
              p-5
            "
          >
            <div className="citypulse-eyebrow">
              Measured PM2.5
            </div>

            <div className="mt-2 flex items-end gap-2">
              <span className="text-4xl font-semibold tracking-tight text-white">
                {currentPm25.toFixed(1)}
              </span>

              <span className="mb-1 text-xs text-muted-foreground">
                µg/m³
              </span>
            </div>

            <div className="mt-3 flex items-center gap-2 text-[11px] text-muted-foreground">
              <Activity className="size-3 text-primary" />
              Observed at prediction time
            </div>
          </div>

          <div
            className="
              hidden size-11
              items-center justify-center
              rounded-full
              border border-primary/30
              bg-primary/10
              text-primary
              md:flex
            "
          >
            <ArrowRight className="size-5" />
          </div>

          <div
            className="
              rounded-xl
              border border-primary/30
              bg-primary/7
              p-5
              citypulse-gold-glow
            "
          >
            <div className="citypulse-eyebrow">
              Predicted +1 Hour
            </div>

            <div className="mt-2 flex items-end gap-2">
              <span className="citypulse-value text-4xl font-semibold tracking-tight">
                {predictedPm25.toFixed(2)}
              </span>

              <span className="mb-1 text-xs text-muted-foreground">
                µg/m³
              </span>
            </div>

            <div className="mt-3 text-[11px] text-primary">
              {difference >= 0 ? "+" : ""}
              {difference.toFixed(2)} µg/m³{" "}
              ({percentChange >= 0 ? "+" : ""}
              {percentChange.toFixed(1)}%)
            </div>
          </div>
        </div>

        <div
          className="
            mt-5 flex flex-wrap
            items-center justify-between
            gap-3 rounded-xl
            border border-primary/10
            bg-black/10
            px-4 py-3
          "
        >
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <MapPin className="size-3.5 text-primary" />

            Selected supported OpenAQ monitoring location · Lahore
          </div>

          <div className="text-[11px] text-muted-foreground">
            Station-based prediction · not citywide ground truth
          </div>
        </div>
      </div>
    </section>
  )
}