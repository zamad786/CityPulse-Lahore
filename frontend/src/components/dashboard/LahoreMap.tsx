import {
  useState,
} from "react"

import {
  CircleMarker,
  MapContainer,
  Popup,
  TileLayer,
  useMapEvents,
} from "react-leaflet"

import {
  Crosshair,
  MapPin,
  Radio,
} from "lucide-react"

import {
  fetchNearestStation,
  type NearestStationResponse,
  type SupportedLocation,
} from "@/lib/api"

import "leaflet/dist/leaflet.css"


const LAHORE_CENTER:
[number, number] = [
  31.5204,
  74.3587,
]


type LahoreMapProps = {
  locations:
    SupportedLocation[]

  activeLocationId:
    number

  onLocationSelect:
    (
      locationId: number
    ) => void
}


function MapClickHandler({
  onMapClick,
}: {
  onMapClick:
    (
      latitude: number,
      longitude: number
    ) => void
}) {

  useMapEvents({
    click(event) {
      onMapClick(
        event.latlng.lat,
        event.latlng.lng
      )
    },
  })


  return null
}


export function LahoreMap({
  locations,
  activeLocationId,
  onLocationSelect,
}: LahoreMapProps) {

  const [
    nearestResult,
    setNearestResult,
  ] = useState<
    NearestStationResponse
    | null
  >(null)


  const [
    locating,
    setLocating,
  ] = useState(false)


  const [
    mapError,
    setMapError,
  ] = useState<
    string | null
  >(null)


  const activeStation =
    locations.find(
      location =>
        location.location_id
        === activeLocationId
    )


  async function handleMapClick(
    latitude: number,
    longitude: number
  ) {
    try {
      setLocating(true)
      setMapError(null)

      const result =
        await fetchNearestStation(
          latitude,
          longitude
        )

      setNearestResult(
        result
      )

      onLocationSelect(
        result
          .nearest_station
          .location_id
      )
    }
    catch (error) {
      console.error(
        error
      )

      setMapError(
        "Unable to identify the nearest supported station."
      )
    }
    finally {
      setLocating(false)
    }
  }


  return (
    <section
      className="
        self-start
        overflow-hidden
        rounded-2xl
        citypulse-panel
      "
    >
      <div
        className="
          flex flex-wrap
          items-start justify-between
          gap-4
          p-6 pb-4
        "
      >
        <div>
          <div className="flex items-center gap-2">
            <MapPin className="size-4 text-primary" />

            <span className="citypulse-eyebrow">
              Lahore Spatial Intelligence
            </span>
          </div>

          <h2 className="mt-2 text-lg font-semibold text-white">
            Select Prediction Location
          </h2>

          <p className="mt-1 max-w-2xl text-xs leading-5 text-muted-foreground">
            Click a supported station directly,
            or click anywhere in Lahore and CityPulse
            will activate the nearest supported
            monitoring station.
          </p>
        </div>


        <div
          className="
            flex max-w-full
            items-center gap-2
            rounded-full
            border border-primary/25
            bg-primary/7
            px-3 py-1.5
            text-[11px]
            text-primary
          "
        >
          <Radio className="size-3 shrink-0" />

          <span className="truncate">
            {
              locating
                ? "Finding nearest station..."
                : activeStation?.name
                  ?? "No active station"
            }
          </span>
        </div>
      </div>


      <div className="mx-6 citypulse-gold-line" />


      <div
        className="
          relative
          mx-3 mb-4 mt-5
          overflow-hidden
          rounded-xl
          border border-primary/20
          sm:mx-6
          sm:mb-6
        "
      >
        <MapContainer
          center={
            LAHORE_CENTER
          }
          zoom={11}
          scrollWheelZoom
          className="
            h-72 w-full
            sm:h-80
            lg:h-97.5
          "
        >
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />


          <MapClickHandler
            onMapClick={
              handleMapClick
            }
          />


          {locations.map(
            location => {
              const active =
                location.location_id
                === activeLocationId


              return (
                <CircleMarker
                  key={
                    location.location_id
                  }
                  center={[
                    location.latitude,
                    location.longitude,
                  ]}
                  radius={
                    active
                      ? 13
                      : 8
                  }
                  bubblingMouseEvents={
                    false
                  }
                  pathOptions={{
                    color:
                      active
                        ? "#f0ca67"
                        : "#8493a7",

                    fillColor:
                      active
                        ? "#d6b458"
                        : "#52657c",

                    fillOpacity:
                      active
                        ? 0.82
                        : 0.58,

                    weight:
                      active
                        ? 3
                        : 2,
                  }}
                  eventHandlers={{
                    click: () => {
                      setNearestResult(
                        null
                      )

                      setMapError(
                        null
                      )

                      onLocationSelect(
                        location.location_id
                      )
                    },
                  }}
                >
                  <Popup>
                    <div
                      style={{
                        minWidth:
                          "220px",
                      }}
                    >
                      <strong>
                        {location.name}
                      </strong>

                      <br />
                      <br />

                      <strong>
                        Status:
                      </strong>{" "}

                      {
                        active
                          ? "Active intelligence station"
                          : "Supported CityPulse station"
                      }

                      <br />

                      <strong>
                        OpenAQ ID:
                      </strong>{" "}

                      {
                        location.location_id
                      }

                      <br />

                      <strong>
                        Sensor ID:
                      </strong>{" "}

                      {
                        location.sensor_id
                      }

                      <br />

                      <strong>
                        Provider:
                      </strong>{" "}

                      {
                        location.provider
                        ?? "OpenAQ"
                      }

                      <br />
                      <br />

                      Click the marker to use
                      this station for forecasting.
                    </div>
                  </Popup>
                </CircleMarker>
              )
            }
          )}


          {nearestResult && (
            <CircleMarker
              center={[
                nearestResult
                  .selected_point
                  .latitude,

                nearestResult
                  .selected_point
                  .longitude,
              ]}
              radius={7}
              bubblingMouseEvents={
                false
              }
              pathOptions={{
                color:
                  "#7da7d9",

                fillColor:
                  "#7da7d9",

                fillOpacity:
                  0.75,

                weight:
                  2,
              }}
            >
              <Popup>
                <div
                  style={{
                    minWidth:
                      "210px",
                  }}
                >
                  <strong>
                    Selected Location
                  </strong>

                  <br />
                  <br />

                  Nearest supported station:

                  <br />

                  <strong>
                    {
                      nearestResult
                        .nearest_station
                        .name
                    }
                  </strong>

                  <br />
                  <br />

                  Distance:{" "}
                  {
                    nearestResult
                      .distance_km
                  }{" "}
                  km
                </div>
              </Popup>
            </CircleMarker>
          )}
        </MapContainer>


        <div
          className="
            pointer-events-none
            absolute
            bottom-3 left-3
            z-500
            max-w-[75%]
            rounded-lg
            border border-primary/25
            bg-[#07111f]/90
            px-3 py-2
            backdrop-blur-xl
          "
        >
          <div className="citypulse-eyebrow">
            Active Intelligence
          </div>

          <div className="mt-1 truncate text-[11px] text-white">
            {
              locating
                ? "Finding nearest supported station..."
                : activeStation?.name
            }
          </div>
        </div>
      </div>


      {nearestResult && (
        <div className="px-6 pb-4">
          <div
            className="
              flex items-start gap-3
              rounded-xl
              border border-[#7da7d9]/25
              bg-[#7da7d9]/5
              px-4 py-3
            "
          >
            <Crosshair className="mt-0.5 size-4 shrink-0 text-[#9ebee3]" />

            <div>
              <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#9ebee3]">
                Nearest Supported Station Mode
              </div>

              <div className="mt-1 text-xs leading-5 text-white">
                {
                  nearestResult
                    .nearest_station
                    .name
                }
                {" · "}
                {
                  nearestResult
                    .distance_km
                }{" "}
                km from your selected point
              </div>
            </div>
          </div>
        </div>
      )}


      {mapError && (
        <div className="px-6 pb-4 text-xs text-red-300">
          {mapError}
        </div>
      )}


      <div className="px-6 pb-6">
        <div
          className="
            rounded-xl
            border border-primary/15
            bg-primary/5
            px-4 py-3
            text-[11px]
            leading-5
            text-muted-foreground
          "
        >
          <span className="font-medium text-primary">
            Gold
          </span>
          {" "}
          = active prediction station.
          {" "}

          Gray = other supported CityPulse stations.
          {" "}

          <span className="font-medium text-[#9ebee3]">
            Blue
          </span>
          {" "}
          = user-selected point mapped to its nearest
          supported monitoring station.
        </div>
      </div>
    </section>
  )
}