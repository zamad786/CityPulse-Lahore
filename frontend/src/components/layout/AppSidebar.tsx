import type { LucideIcon } from "lucide-react"

import {
  Activity,
  BellRing,
  BrainCircuit,
  Database,
  LayoutDashboard,
  MapPinned,
  Radar,
  TrendingUp,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"


type NavItem = {
  id: string
  label: string
  description: string
  icon: LucideIcon
}


const NAV_ITEMS: NavItem[] = [
  {
    id: "command-centre",
    label: "Command Centre",
    description: "Live city overview",
    icon: LayoutDashboard,
  },
  {
    id: "forecast",
    label: "Forecast Intelligence",
    description: "AI PM2.5 outlook",
    icon: TrendingUp,
  },
  {
    id: "map",
    label: "Lahore Map",
    description: "Spatial intelligence",
    icon: MapPinned,
  },
  {
    id: "alerts",
    label: "Risk Alerts",
    description: "Citizen warnings",
    icon: BellRing,
  },
  {
    id: "model",
    label: "Data & Model",
    description: "Prediction system",
    icon: Database,
  },
]


type AppSidebarProps = {
  activeItem: string
  onSelect: (id: string) => void
}


export function AppSidebar({
  activeItem,
  onSelect,
}: AppSidebarProps) {
  return (
    <aside
      className="
        fixed inset-y-0 left-0 z-40 hidden
        w-70 flex-col
        border-r border-primary/20
        bg-sidebar/95
        shadow-[18px_0_60px_rgba(0,0,0,0.22)]
        backdrop-blur-xl
        lg:flex
      "
    >
      <div className="px-5 pt-6">
        <div className="flex items-center gap-3">
          <div
            className="
              relative flex size-12
              items-center justify-center
              rounded-2xl
              border border-primary/35
              bg-primary/10
              citypulse-gold-glow
            "
          >
            <Radar
              className="size-6 text-primary"
              strokeWidth={1.8}
            />

            <span
              className="
                absolute right-1.5 top-1.5
                size-2 rounded-full
                bg-primary
                shadow-[0_0_14px_rgba(214,180,88,0.9)]
              "
            />
          </div>

          <div>
            <div className="citypulse-eyebrow">
              City Intelligence
            </div>

            <div className="mt-1 text-lg font-semibold tracking-tight text-white">
              CityPulse
              <span className="text-primary">
                {" "}Lahore
              </span>
            </div>
          </div>
        </div>

        <div
          className="
            mt-5 rounded-xl
            border border-primary/20
            bg-primary/5
            px-3 py-3
          "
        >
          <div className="flex items-center gap-2 text-xs font-medium text-primary">
            <Activity className="size-3.5" />
            Predictive Urban Intelligence
          </div>

          <p className="mt-1.5 text-[11px] leading-5 text-muted-foreground">
            Monitoring → Prediction → Risk → Action
          </p>
        </div>
      </div>

      <div className="my-5 citypulse-gold-line" />

      <nav className="flex-1 space-y-1 px-3">
        <div className="mb-3 px-3 citypulse-eyebrow">
          Intelligence Modules
        </div>

        {NAV_ITEMS.map((item) => {
          const Icon = item.icon
          const active =
            activeItem === item.id

          return (
            <Button
              key={item.id}
              variant="ghost"
              onClick={() =>
                onSelect(item.id)
              }
              className={`
                group h-auto w-full
                justify-start rounded-xl
                border px-3 py-3
                text-left
                transition-all duration-200

                ${
                  active
                    ? "border-primary/35 bg-primary/10 text-primary shadow-[0_0_24px_rgba(214,180,88,0.06)] hover:bg-primary/10 hover:text-primary"
                    : "border-transparent text-sidebar-foreground/75 hover:border-primary/15 hover:bg-primary/5 hover:text-primary"
                }
              `}
            >
              <div
                className={`
                  mr-3 flex size-9 shrink-0
                  items-center justify-center
                  rounded-lg border
                  transition-all

                  ${
                    active
                      ? "border-primary/30 bg-primary/15 text-primary"
                      : "border-white/5 bg-white/3 text-muted-foreground group-hover:border-primary/20 group-hover:text-primary"
                  }
                `}
              >
                <Icon
                  className="size-4.5"
                  strokeWidth={1.8}
                />
              </div>

              <div className="min-w-0">
                <div className="text-[13px] font-medium">
                  {item.label}
                </div>

                <div
                  className={`
                    mt-0.5 text-[10px]

                    ${
                      active
                        ? "text-primary/65"
                        : "text-muted-foreground"
                    }
                  `}
                >
                  {item.description}
                </div>
              </div>
            </Button>
          )
        })}
      </nav>

      <div className="px-4 pb-5">
        <Separator className="mb-4 bg-primary/15" />

        <div
          className="
            rounded-xl
            border border-primary/20
            bg-primary/5
            p-3
          "
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BrainCircuit className="size-4 text-primary" />

              <span className="text-xs font-medium text-white">
                Prediction Engine
              </span>
            </div>

            <span className="relative flex size-2">
              <span
                className="
                  absolute inline-flex size-full
                  animate-ping rounded-full
                  bg-primary opacity-40
                "
              />

              <span
                className="
                  relative inline-flex size-2
                  rounded-full bg-primary
                "
              />
            </span>
          </div>

          <div className="mt-2 flex items-center gap-2 text-[10px] text-muted-foreground">
            <Activity className="size-3 text-primary" />

            Random Forest · 1h Forecast
          </div>
        </div>
      </div>
    </aside>
  )
}