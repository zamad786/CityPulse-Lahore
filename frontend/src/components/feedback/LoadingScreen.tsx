import {
  Activity,
  BrainCircuit,
  MapPinned,
  Radar,
} from "lucide-react"


export function LoadingScreen() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div
        className="
          citypulse-grid
          flex min-h-screen
          items-center justify-center
          px-4 py-10
        "
      >
        <div className="w-full max-w-3xl">
          <div
            className="
              relative overflow-hidden
              rounded-2xl
              p-7
              citypulse-panel-strong
              sm:p-10
            "
          >
            <div
              className="
                pointer-events-none
                absolute -right-20 -top-20
                size-72 rounded-full
                bg-primary/10 blur-3xl
              "
            />

            <div className="relative text-center">
              <div
                className="
                  relative mx-auto
                  flex size-20
                  items-center justify-center
                  rounded-full
                  border border-primary/30
                  bg-primary/8
                  citypulse-gold-glow
                "
              >
                <span
                  className="
                    absolute inset-2
                    animate-ping
                    rounded-full
                    border border-primary/20
                  "
                />

                <Radar className="size-9 animate-pulse text-primary" />
              </div>

              <div className="mt-6 citypulse-eyebrow">
                CityPulse Lahore
              </div>

              <h1 className="mt-2 text-2xl font-semibold text-white">
                Loading Urban Intelligence
              </h1>

              <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-muted-foreground">
                Retrieving the latest available PM2.5 observation,
                weather features, forecast and citizen risk intelligence.
              </p>

              <div
                className="
                  mx-auto mt-7 grid
                  max-w-xl gap-3
                  sm:grid-cols-3
                "
              >
                <LoadingItem
                  icon={Activity}
                  text="Monitoring"
                />

                <LoadingItem
                  icon={BrainCircuit}
                  text="Prediction"
                />

                <LoadingItem
                  icon={MapPinned}
                  text="Risk Intelligence"
                />
              </div>

              <div className="mx-auto mt-7 h-1.5 max-w-md overflow-hidden rounded-full bg-primary/10">
                <div
                  className="
                    h-full w-1/2
                    animate-pulse
                    rounded-full
                    bg-primary
                  "
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}


function LoadingItem({
  icon: Icon,
  text,
}: {
  icon: typeof Activity
  text: string
}) {
  return (
    <div
      className="
        flex items-center justify-center
        gap-2 rounded-xl
        border border-primary/15
        bg-primary/5
        px-3 py-3
        text-xs text-muted-foreground
      "
    >
      <Icon className="size-4 text-primary" />

      {text}
    </div>
  )
}