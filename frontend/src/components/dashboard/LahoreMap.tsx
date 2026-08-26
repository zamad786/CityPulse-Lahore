import {
  useState,
} from "react"

import {
  Circle,
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  useMapEvents,
} from "react-leaflet"

import {
  divIcon,
} from "leaflet"

import {
  Crosshair,
  MapPin,
  Radio,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react"

import {
  fetchNearestStation,
  type NearestStationResponse,
  type SupportedLocation,
} from "@/lib/api"

import "leaflet/dist/leaflet.css"


// =========================================================
// MAP SETTINGS
// =========================================================

const LAHORE_CENTER:
[number, number] = [
  31.5204,
  74.3587,
]


const COVERAGE_RADIUS_KM = 5

const COVERAGE_RADIUS_METERS =
  COVERAGE_RADIUS_KM * 1000


// =========================================================
// CUSTOM STATION MARKERS
//
// These replace the old CircleMarker station symbols.
// There are NO permanent geographic coverage circles.
// =========================================================

const activeStationIcon = divIcon({
  className: "",

  html: `
    <div
      style="
        position: relative;
        width: 24px;
        height: 30px;
      "
    >
      <div
        style="
          position: absolute;
          left: 3px;
          top: 1px;
          width: 18px;
          height: 18px;
          transform: rotate(-45deg);
          border-radius: 50% 50% 50% 0;
          background: #d6b458;
          border: 2px solid #f0ca67;
          box-shadow:
            0 0 0 4px rgba(240, 202, 103, 0.14),
            0 5px 12px rgba(0, 0, 0, 0.45);
        "
      >
        <div
          style="
            position: absolute;
            left: 50%;
            top: 50%;
            width: 5px;
            height: 5px;
            transform:
              translate(-50%, -50%);
            border-radius: 50%;
            background: #07111f;
          "
        ></div>
      </div>
    </div>
  `,

  iconSize: [
    24,
    30,
  ],

  iconAnchor: [
    12,
    27,
  ],

  popupAnchor: [
    0,
    -27,
  ],
})


const supportedStationIcon = divIcon({
  className: "",

  html: `
    <div
      style="
        position: relative;
        width: 20px;
        height: 26px;
      "
    >
      <div
        style="
          position: absolute;
          left: 3px;
          top: 2px;
          width: 14px;
          height: 14px;
          transform: rotate(-45deg);
          border-radius: 50% 50% 50% 0;
          background: #52657c;
          border: 2px solid #8493a7;
          box-shadow:
            0 4px 10px rgba(0, 0, 0, 0.35);
        "
      >
        <div
          style="
            position: absolute;
            left: 50%;
            top: 50%;
            width: 4px;
            height: 4px;
            transform:
              translate(-50%, -50%);
            border-radius: 50%;
            background: #d9e3ef;
          "
        ></div>
      </div>
    </div>
  `,

  iconSize: [
    20,
    26,
  ],

  iconAnchor: [
    10,
    23,
  ],

  popupAnchor: [
    0,
    -23,
  ],
})


// =========================================================
// PROPS
// =========================================================

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


// =========================================================
// MAP CLICK HANDLER
// =========================================================

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


// =========================================================
// COMPONENT
// =========================================================

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


  const withinCoverage =
    nearestResult
      ? (
          nearestResult
            .distance_km
          <= COVERAGE_RADIUS_KM
        )
      : true


  // =======================================================
  // CLICK ANYWHERE ON MAP
  // =======================================================

  async function handleMapClick(
    latitude: number,
    longitude: number
  ) {

    try {

      setLocating(
        true
      )

      setMapError(
        null
      )


      const result =
        await fetchNearestStation(
          latitude,
          longitude
        )


      // Replacing this state automatically removes
      // the previous circle and creates the new one.
      setNearestResult(
        result
      )


      // Show the nearest station's real supported
      // observation + prediction data.
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

      setLocating(
        false
      )
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

      {/* ==================================================
          HEADER
      ================================================== */}

      <div
        className="
          flex flex-wrap
          items-start justify-between
          gap-4
          p-6 pb-4
        "
      >

        <div>

          <div
            className="
              flex items-center gap-2
            "
          >

            <MapPin
              className="
                size-4
                text-primary
              "
            />

            <span
              className="
                citypulse-eyebrow
              "
            >
              Lahore Spatial Intelligence
            </span>

          </div>


          <h2
            className="
              mt-2
              text-lg
              font-semibold
              text-white
            "
          >
            Select Prediction Location
          </h2>


          <p
            className="
              mt-1
              max-w-2xl
              text-xs
              leading-5
              text-muted-foreground
            "
          >
            Select one of the{" "}
            {locations.length} supported
            monitoring stations, or click
            anywhere on the map to find the
            nearest station within the
            recommended 5 km coverage radius.
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

          <Radio
            className="
              size-3
              shrink-0
            "
          />

          <span
            className="
              truncate
            "
          >
            {
              locating
                ? "Finding nearest station..."
                : activeStation?.name
                  ?? "No active station"
            }
          </span>

        </div>

      </div>


      <div
        className="
          mx-6
          citypulse-gold-line
        "
      />


      {/* ==================================================
          MAP
      ================================================== */}

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


          {/* ==============================================
              19 SUPPORTED STATION PINS

              These are only pin markers.
              They are NOT geographic coverage circles.
          ============================================== */}

          {
            locations.map(
              location => {

                const active =
                  location.location_id
                  === activeLocationId


                return (
                  <Marker
                    key={
                      location.location_id
                    }

                    position={[
                      location.latitude,
                      location.longitude,
                    ]}

                    icon={
                      active
                        ? activeStationIcon
                        : supportedStationIcon
                    }

                    bubblingMouseEvents={
                      false
                    }

                    eventHandlers={{
                      click: () => {

                        // Clicking an actual station
                        // removes the user-selected
                        // 5 km circle.
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
                        </strong>
                        {" "}

                        {
                          active
                            ? "Active intelligence station"
                            : "Supported CityPulse station"
                        }


                        <br />


                        <strong>
                          OpenAQ ID:
                        </strong>
                        {" "}

                        {
                          location.location_id
                        }


                        <br />


                        <strong>
                          Sensor ID:
                        </strong>
                        {" "}

                        {
                          location.sensor_id
                        }


                        <br />


                        <strong>
                          Provider:
                        </strong>
                        {" "}

                        {
                          location.provider
                          ?? "OpenAQ"
                        }


                        <br />
                        <br />


                        Click this marker to use
                        the station for forecasting.

                      </div>

                    </Popup>

                  </Marker>
                )
              }
            )
          }


          {/* ==============================================
              EXACTLY ONE 5 KM CIRCLE

              Appears ONLY after user clicks the map.

              Clicking somewhere else replaces it.
              Clicking an actual station removes it.
          ============================================== */}

          {
            nearestResult
            && (
              <Circle
                center={[
                  nearestResult
                    .selected_point
                    .latitude,

                  nearestResult
                    .selected_point
                    .longitude,
                ]}

                radius={
                  COVERAGE_RADIUS_METERS
                }

                bubblingMouseEvents={
                  false
                }

                pathOptions={{
                  color:
                    "#6ea8e8",

                  fillColor:
                    "#4e8dcc",

                  fillOpacity:
                    0.10,

                  weight:
                    2,
                }}
              >

                <Popup>

                  <div
                    style={{
                      minWidth:
                        "230px",
                    }}
                  >

                    <strong>
                      Selected Map Location
                    </strong>


                    <br />
                    <br />


                    Search radius:
                    {" "}

                    <strong>
                      {COVERAGE_RADIUS_KM} km
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


                    Distance:
                    {" "}

                    <strong>
                      {
                        nearestResult
                          .distance_km
                      }
                      {" "}
                      km
                    </strong>


                    <br />
                    <br />


                    {
                      withinCoverage
                        ? (
                            <span>
                              Within recommended
                              CityPulse coverage.
                            </span>
                          )
                        : (
                            <span>
                              Outside the recommended
                              5 km coverage radius.
                              Nearest-station data is
                              shown for reference only.
                            </span>
                          )
                    }

                  </div>

                </Popup>

              </Circle>
            )
          }

        </MapContainer>


        {/* ================================================
            ACTIVE LOCATION OVERLAY
        ================================================ */}

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

          <div
            className="
              citypulse-eyebrow
            "
          >
            Active Intelligence
          </div>


          <div
            className="
              mt-1
              truncate
              text-[11px]
              text-white
            "
          >
            {
              locating
                ? "Finding nearest supported station..."
                : activeStation?.name
                  ?? "No station selected"
            }
          </div>

        </div>

      </div>


      {/* ==================================================
          CLICK RESULT / COVERAGE STATUS
      ================================================== */}

      {
        nearestResult
        && (
          <div
            className="
              px-6 pb-4
            "
          >

            <div
              className={`
                flex
                items-start
                gap-3
                rounded-xl
                border
                px-4 py-3

                ${
                  withinCoverage
                    ? `
                      border-[#7da7d9]/25
                      bg-[#7da7d9]/5
                    `
                    : `
                      border-amber-400/30
                      bg-amber-400/5
                    `
                }
              `}
            >

              {
                withinCoverage
                  ? (
                      <ShieldCheck
                        className="
                          mt-0.5
                          size-4
                          shrink-0
                          text-[#9ebee3]
                        "
                      />
                    )
                  : (
                      <TriangleAlert
                        className="
                          mt-0.5
                          size-4
                          shrink-0
                          text-amber-300
                        "
                      />
                    )
              }


              <div>

                <div
                  className={`
                    text-[10px]
                    font-semibold
                    uppercase
                    tracking-[0.18em]

                    ${
                      withinCoverage
                        ? "text-[#9ebee3]"
                        : "text-amber-300"
                    }
                  `}
                >
                  {
                    withinCoverage
                      ? "Within Recommended Coverage"
                      : "Outside Recommended Coverage"
                  }
                </div>


                <div
                  className="
                    mt-1
                    text-xs
                    leading-5
                    text-white
                  "
                >

                  {
                    nearestResult
                      .nearest_station
                      .name
                  }

                  {" · "}

                  {
                    nearestResult
                      .distance_km
                  }

                  {" "}
                  km from your selected point.

                </div>


                {
                  !withinCoverage
                  && (
                    <div
                      className="
                        mt-1
                        text-[11px]
                        leading-5
                        text-muted-foreground
                      "
                    >
                      This location is more than
                      5 km from the nearest supported
                      monitoring station. CityPulse
                      is showing the nearest station
                      as a reference and is not
                      claiming an exact measurement
                      at the clicked point.
                    </div>
                  )
                }

              </div>

            </div>

          </div>
        )
      }


      {/* ==================================================
          ERROR
      ================================================== */}

      {
        mapError
        && (
          <div
            className="
              px-6 pb-4
              text-xs
              text-red-300
            "
          >
            {mapError}
          </div>
        )
      }


      {/* ==================================================
          LEGEND
      ================================================== */}

      <div
        className="
          px-6 pb-6
        "
      >

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

          <span
            className="
              font-medium
              text-primary
            "
          >
            Gold pin
          </span>

          {" "}
          = active prediction station.
          {" "}


          Gray pins = other supported
          CityPulse monitoring stations.
          {" "}


          <span
            className="
              font-medium
              text-[#9ebee3]
            "
          >
            Blue circle
          </span>

          {" "}
          = the single 5 km search radius
          created only after a user clicks
          the map.

        </div>

      </div>

    </section>
  )
}
