import {
  LoaderCircle,
  MapPin,
  Radio,
} from "lucide-react"

import type {
  SupportedLocation,
} from "@/lib/api"


type LocationSelectorProps = {
  locations:
    SupportedLocation[]

  activeLocationId:
    number

  switching?:
    boolean

  onSelect:
    (
      locationId: number
    ) => void
}


export function LocationSelector({
  locations,
  activeLocationId,
  switching = false,
  onSelect,
}: LocationSelectorProps) {

  const activeLocation =
    locations.find(
      location =>
        location.location_id
        === activeLocationId
    )


  return (
    <section
      className="
        mb-5
        flex flex-col gap-4
        rounded-2xl
        border border-primary/15
        bg-card/75
        px-4 py-4
        backdrop-blur-xl
        sm:flex-row
        sm:items-center
        sm:justify-between
      "
    >
      <div className="flex min-w-0 items-center gap-3">
        <div className="citypulse-icon-box size-10 shrink-0">
          <MapPin className="size-4" />
        </div>

        <div className="min-w-0">
          <div className="citypulse-eyebrow">
            Active Intelligence Location
          </div>

          <div className="mt-1 truncate text-sm font-semibold text-white">
            {
              activeLocation?.name
              ?? "Select Lahore station"
            }
          </div>

          <div className="mt-1 flex items-center gap-1.5 text-[10px] text-muted-foreground">
            <Radio className="size-3 text-primary" />

            {locations.length} supported Lahore monitoring locations
          </div>
        </div>
      </div>


      <div className="flex items-center gap-3">
        {switching && (
          <div className="flex items-center gap-2 text-[10px] text-primary">
            <LoaderCircle className="size-3.5 animate-spin" />

            Updating intelligence
          </div>
        )}


        <select
          aria-label="Select CityPulse monitoring location"
          value={
            activeLocationId
          }
          disabled={
            switching
            || locations.length === 0
          }
          onChange={
            event => {
              onSelect(
                Number(
                  event.target.value
                )
              )
            }
          }
          className="
            min-h-11
            w-full
            rounded-xl
            border border-primary/20
            bg-[#07111f]
            px-3
            text-xs
            font-medium
            text-white
            outline-none
            transition
            focus:border-primary/50
            disabled:cursor-wait
            disabled:opacity-60
            sm:w-72
          "
        >
          {locations.map(
            location => (
              <option
                key={
                  location.location_id
                }
                value={
                  location.location_id
                }
              >
                {location.name}
              </option>
            )
          )}
        </select>
      </div>
    </section>
  )
}
