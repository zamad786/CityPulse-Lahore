import {
  BellRing,
  Eye,
  HeartPulse,
  MapPin,
  Sparkles,
} from "lucide-react"


type AlertPanelProps = {
  level: string
  recommendation: string
}


export function AlertPanel({
  level,
  recommendation,
}: AlertPanelProps) {
  return (
    <section
      id="risk-alerts"
      className="
        rounded-2xl p-6
        citypulse-panel-strong
      "
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <BellRing className="size-4 text-primary" />

            <span className="citypulse-eyebrow">
              Citizen Alert
            </span>
          </div>

          <h2 className="mt-2 text-lg font-semibold text-white">
            Recommended Action
          </h2>
        </div>

        <div
          className="
            flex size-10
            items-center justify-center
            rounded-xl
            border border-primary/25
            bg-primary/10
          "
        >
          <Sparkles className="size-5 text-primary" />
        </div>
      </div>

      <div className="my-5 citypulse-gold-line" />

      <div
        className="
          rounded-xl
          border border-primary/25
          bg-primary/8
          p-5
        "
      >
        <div className="text-sm font-semibold text-primary">
          {level} PM2.5 conditions predicted
        </div>

        <p className="mt-2 text-xs leading-6 text-muted-foreground">
          {recommendation}
        </p>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <AlertItem
          icon={Eye}
          title="Monitor"
          text="Check updated PM2.5 forecasts."
        />

        <AlertItem
          icon={HeartPulse}
          title="Protect"
          text="Sensitive groups should manage exposure."
        />

        <AlertItem
          icon={MapPin}
          title="Location"
          text="Current intelligence uses the selected supported Lahore monitoring station."
        />
      </div>

      <div className="mt-4 text-[10px] leading-5 text-muted-foreground">
        CityPulse recommendations are decision-support guidance based
        on predicted PM2.5 risk and do not replace official emergency
        or medical advice.
      </div>
    </section>
  )
}


function AlertItem({
  icon: Icon,
  title,
  text,
}: {
  icon: typeof Eye
  title: string
  text: string
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
      <Icon className="size-4 text-primary" />

      <div className="mt-3 text-xs font-semibold text-white">
        {title}
      </div>

      <div className="mt-1 text-[10px] leading-5 text-muted-foreground">
        {text}
      </div>
    </div>
  )
}