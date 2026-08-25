import {
  ShieldAlert,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react"


type RiskPanelProps = {
  predictedPm25: number
  level: string
  responseStage: string
  referenceBand: string
  recommendation: string
}


export function RiskPanel({
  predictedPm25,
  level,
  responseStage,
  referenceBand,
  recommendation,
}: RiskPanelProps) {
  return (
    <section
      id="risk-intelligence"
      className="
        relative overflow-hidden
        rounded-2xl p-6
        citypulse-panel
      "
    >
      <div
        className="
          absolute -right-16 -top-16
          size-52 rounded-full
          bg-primary/7 blur-3xl
        "
      />

      <div className="relative">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <ShieldAlert className="size-4 text-primary" />

              <span className="citypulse-eyebrow">
                Urban Risk Intelligence
              </span>
            </div>

            <h2 className="mt-2 text-lg font-semibold text-white">
              Forecast Risk Assessment
            </h2>
          </div>

          <div
            className="
              rounded-full
              border border-primary/30
              bg-primary/10
              px-3 py-1.5
              text-xs font-semibold
              text-primary
            "
          >
            {level}
          </div>
        </div>

        <div className="my-5 citypulse-gold-line" />

        <div className="grid gap-3 sm:grid-cols-3">
          <RiskMetric
            label="Predicted PM2.5"
            value={`${predictedPm25.toFixed(2)} µg/m³`}
          />

          <RiskMetric
            label="Response Stage"
            value={responseStage}
          />

          <RiskMetric
            label="AQI Reference Band"
            value={referenceBand}
          />
        </div>

        <div
          className="
            mt-5 rounded-xl
            border border-primary/20
            bg-primary/6
            p-4
          "
        >
          <div className="flex items-start gap-3">
            <TriangleAlert className="mt-0.5 size-5 shrink-0 text-primary" />

            <div>
              <div className="text-sm font-medium text-white">
                Risk Interpretation
              </div>

              <p className="mt-1 text-xs leading-6 text-muted-foreground">
                {recommendation}
              </p>
            </div>
          </div>
        </div>

        <div className="mt-4 flex items-start gap-2 text-[10px] leading-5 text-muted-foreground">
          <ShieldCheck className="mt-0.5 size-3.5 shrink-0 text-primary" />

          Forecast classification uses Punjab EPA PM2.5
          breakpoint bands for CityPulse risk intelligence.
          It is not presented as an official regulatory AQI reading.
        </div>
      </div>
    </section>
  )
}


function RiskMetric({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div
      className="
        rounded-xl
        border border-primary/15
        bg-black/10
        p-4
      "
    >
      <div className="citypulse-eyebrow">
        {label}
      </div>

      <div className="mt-2 text-sm font-semibold text-white">
        {value}
      </div>
    </div>
  )
}