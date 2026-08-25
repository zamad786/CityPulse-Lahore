import {
  BellRing,
  Database,
  LayoutDashboard,
  MapPinned,
  TrendingUp,
} from "lucide-react"


type MobileNavProps = {
  activeItem: string
  onSelect: (id: string) => void
}


const ITEMS = [
  {
    id: "command-centre",
    label: "Home",
    icon: LayoutDashboard,
  },
  {
    id: "forecast",
    label: "Forecast",
    icon: TrendingUp,
  },
  {
    id: "map",
    label: "Map",
    icon: MapPinned,
  },
  {
    id: "alerts",
    label: "Alerts",
    icon: BellRing,
  },
  {
    id: "model",
    label: "Model",
    icon: Database,
  },
]


export function MobileNav({
  activeItem,
  onSelect,
}: MobileNavProps) {
  return (
    <nav
      className="
        fixed inset-x-3 bottom-3 z-[1000]
        grid grid-cols-5
        rounded-2xl
        border border-primary/25
        bg-[#07111f]/95
        p-1.5
        shadow-[0_18px_60px_rgba(0,0,0,0.45)]
        backdrop-blur-xl
        lg:hidden
      "
    >
      {ITEMS.map((item) => {
        const Icon = item.icon
        const active =
          activeItem === item.id

        return (
          <button
            key={item.id}
            type="button"
            onClick={() =>
              onSelect(item.id)
            }
            className={`
              flex min-w-0 flex-col
              items-center justify-center
              gap-1 rounded-xl
              px-1 py-2
              text-[9px] font-medium
              transition-all

              ${
                active
                  ? "bg-primary/12 text-primary"
                  : "text-muted-foreground hover:bg-primary/5 hover:text-primary"
              }
            `}
          >
            <Icon
              className={`
                size-4.5
                ${
                  active
                    ? "text-primary"
                    : ""
                }
              `}
            />

            <span className="truncate">
              {item.label}
            </span>
          </button>
        )
      })}
    </nav>
  )
}