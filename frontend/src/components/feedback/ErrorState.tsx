import {
  RefreshCw,
  ServerOff,
  ShieldAlert,
} from "lucide-react"

import { Button } from "@/components/ui/button"


type ErrorStateProps = {
  message: string
  onRetry: () => void
}


export function ErrorState({
  message,
  onRetry,
}: ErrorStateProps) {
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
        <div
          className="
            w-full max-w-xl
            rounded-2xl p-7
            citypulse-panel-strong
            sm:p-9
          "
        >
          <div
            className="
              mx-auto flex size-16
              items-center justify-center
              rounded-2xl
              border border-primary/25
              bg-primary/8
            "
          >
            <ServerOff className="size-7 text-primary" />
          </div>

          <div className="mt-6 text-center">
            <div className="citypulse-eyebrow">
              Connection Interrupted
            </div>

            <h1 className="mt-2 text-2xl font-semibold text-white">
              CityPulse API unavailable
            </h1>

            <p className="mt-3 text-sm leading-6 text-muted-foreground">
              The dashboard could not retrieve prediction intelligence
              from the FastAPI backend.
            </p>
          </div>

          <div
            className="
              mt-6 rounded-xl
              border border-primary/20
              bg-primary/5
              p-4
            "
          >
            <div className="flex items-start gap-3">
              <ShieldAlert className="mt-0.5 size-4 shrink-0 text-primary" />

              <div>
                <div className="text-xs font-medium text-white">
                  Connection details
                </div>

                <div className="mt-1 break-words text-[11px] leading-5 text-muted-foreground">
                  {message}
                </div>
              </div>
            </div>
          </div>

          <Button
            type="button"
            onClick={onRetry}
            className="
              mt-6 w-full
              bg-primary
              text-primary-foreground
              hover:bg-primary/90
            "
          >
            <RefreshCw className="mr-2 size-4" />
            Retry Connection
          </Button>

          <p className="mt-4 text-center text-[10px] leading-5 text-muted-foreground">
            During local development, make sure FastAPI is running at
            http://127.0.0.1:8000.
          </p>
        </div>
      </div>
    </div>
  )
}