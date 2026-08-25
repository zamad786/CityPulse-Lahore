import {
  BrainCircuit,
  Clock3,
  Server,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"


type TopBarProps = {
  pageTitle: string
}


export function TopBar({
  pageTitle,
}: TopBarProps) {
  return (
    <header
      className="
        sticky top-0 z-900
        border-b border-primary/20
        bg-background/90
        backdrop-blur-xl
      "
    >
      <div
        className="
          flex min-h-16
          items-center justify-between
          gap-3 px-4
          sm:min-h-19
          sm:px-5
          lg:px-8
        "
      >
        <div className="min-w-0">
          <div
            className="
              hidden
              citypulse-eyebrow
              sm:block
            "
          >
            Lahore Urban Intelligence Network
          </div>

          <div
            className="
              citypulse-eyebrow
              sm:hidden
            "
          >
            CityPulse Lahore
          </div>

          <h1
            className="
              mt-1 truncate
              text-base font-semibold
              tracking-tight
              text-white
              sm:text-xl
            "
          >
            {pageTitle}
          </h1>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <Badge
            variant="outline"
            className="
              hidden gap-1.5
              border-primary/25
              bg-primary/7
              px-3 py-1.5
              text-primary
              xl:flex
            "
          >
            <Server className="size-3" />
            API Connected
          </Badge>

          <Badge
            variant="outline"
            className="
              hidden gap-1.5
              border-primary/25
              bg-primary/7
              px-3 py-1.5
              text-primary
              lg:flex
            "
          >
            <BrainCircuit className="size-3" />
            Model Ready
          </Badge>

          <div
            className="
              hidden h-6 w-px
              bg-primary/20
              md:block
            "
          />

          <div
            className="
              flex items-center gap-1.5
              text-[10px]
              text-muted-foreground
              sm:text-xs
            "
          >
            <Clock3 className="size-3.5 text-primary" />

            <span className="hidden sm:inline">
              Lahore · PKT
            </span>

            <span className="sm:hidden">
              PKT
            </span>
          </div>
        </div>
      </div>

      <div className="citypulse-gold-line" />
    </header>
  )
}