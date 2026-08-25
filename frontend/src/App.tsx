import {
  useCallback,
  useEffect,
  useState,
} from "react"

import {
  Activity,
  BrainCircuit,
  Clock3,
  Database,
  Droplets,
  MapPin,
  ShieldAlert,
  Thermometer,
  Wind,
} from "lucide-react"

import {
  fetchDashboardData,
  fetchSupportedLocations,
  type DashboardData,
  type SupportedLocation,
} from "@/lib/api"

import {
  LocationSelector,
} from "@/components/dashboard/LocationSelector"

import { AppSidebar } from "@/components/layout/AppSidebar"
import { MobileNav } from "@/components/layout/MobileNav"
import { TopBar } from "@/components/layout/TopBar"

import { AlertPanel } from "@/components/dashboard/AlertPanel"
import { ForecastChart } from "@/components/dashboard/ForecastChart"
import { KpiCard } from "@/components/dashboard/KpiCard"
import { LahoreMap } from "@/components/dashboard/LahoreMap"
import { PredictionPanel } from "@/components/dashboard/PredictionPanel"
import { RiskPanel } from "@/components/dashboard/RiskPanel"

import { ErrorState } from "@/components/feedback/ErrorState"
import { LoadingScreen } from "@/components/feedback/LoadingScreen"

import { Badge } from "@/components/ui/badge"


const DEFAULT_LOCATION_ID =
  4757305


const PAGE_TITLES:
Record<string, string> = {
  "command-centre":
    "Smart City Command Centre",

  forecast:
    "Forecast Intelligence",

  map:
    "Lahore Spatial Intelligence",

  alerts:
    "Urban Risk Alerts",

  model:
    "Data & Model Intelligence",
}


const VALID_VIEWS = [
  "command-centre",
  "forecast",
  "map",
  "alerts",
  "model",
]


function getInitialView() {
  const hash =
    window.location.hash.replace(
      "#",
      ""
    )

  return VALID_VIEWS.includes(
    hash
  )
    ? hash
    : "command-centre"
}


function formatLahoreTime(
  timestamp: string
) {
  return new Intl.DateTimeFormat(
    "en-PK",
    {
      timeZone:
        "Asia/Karachi",

      dateStyle:
        "medium",

      timeStyle:
        "short",
    }
  ).format(
    new Date(
      timestamp
    )
  )
}


/* =========================================================
   APP
   ========================================================= */

function App() {
  const [
    activeItem,
    setActiveItem,
  ] = useState(
    getInitialView
  )


  const [
    locations,
    setLocations,
  ] = useState<
    SupportedLocation[]
  >([])


  const [
    selectedLocationId,
    setSelectedLocationId,
  ] = useState<number>(
    DEFAULT_LOCATION_ID
  )


  const [
    switchingLocation,
    setSwitchingLocation,
  ] = useState(
    false
  )


  const [
    dashboard,
    setDashboard,
  ] = useState<
    DashboardData | null
  >(null)


  const [
    loading,
    setLoading,
  ] = useState(
    true
  )


  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null)


  /* =======================================================
     INITIAL APPLICATION LOAD
     ======================================================= */

  const loadDashboard =
    useCallback(
      async () => {
        try {
          setLoading(
            true
          )

          setError(
            null
          )


          const [
            locationData,
            dashboardData,
          ] = await Promise.all([
            fetchSupportedLocations(),

            fetchDashboardData(
              DEFAULT_LOCATION_ID
            ),
          ])


          setLocations(
            locationData.locations
          )


          setDashboard(
            dashboardData
          )


          setSelectedLocationId(
            dashboardData
              .station
              .location_id
          )
        }
        catch (err) {
          const message =
            err instanceof Error
              ? err.message
              : (
                "Unable to load "
                + "CityPulse intelligence."
              )


          setError(
            message
          )
        }
        finally {
          setLoading(
            false
          )
        }
      },
      []
    )


  useEffect(
    () => {
      void loadDashboard()
    },
    [
      loadDashboard,
    ]
  )


  /* =======================================================
     GLOBAL LOCATION SWITCHING

     This is the important part.

     Every supported location selection reloads the
     location-specific dashboard from FastAPI.

     Therefore ALL views use the same station.
     ======================================================= */

  const handleLocationSelect =
    useCallback(
      async (
        locationId: number
      ) => {
        if (
          locationId
          === selectedLocationId
        ) {
          return
        }


        try {
          setSwitchingLocation(
            true
          )


          const data =
            await fetchDashboardData(
              locationId
            )


          setDashboard(
            data
          )


          setSelectedLocationId(
            data
              .station
              .location_id
          )
        }
        catch (err) {
          console.error(
            "CityPulse location switch failed:",
            err
          )
        }
        finally {
          setSwitchingLocation(
            false
          )
        }
      },
      [
        selectedLocationId,
      ]
    )


  /* =======================================================
     HASH-BASED APPLICATION NAVIGATION
     ======================================================= */

  useEffect(
    () => {
      function handleHashChange() {
        const nextView =
          window
            .location
            .hash
            .replace(
              "#",
              ""
            )


        if (
          VALID_VIEWS.includes(
            nextView
          )
        ) {
          setActiveItem(
            nextView
          )
        }
      }


      window.addEventListener(
        "hashchange",
        handleHashChange
      )


      return () => {
        window.removeEventListener(
          "hashchange",
          handleHashChange
        )
      }
    },
    []
  )


  function handleNavigation(
    id: string
  ) {
    setActiveItem(
      id
    )


    window.history.pushState(
      null,
      "",
      `#${id}`
    )


    window.scrollTo({
      top: 0,
      behavior: "smooth",
    })
  }


  /* =======================================================
     LOADING / ERROR
     ======================================================= */

  if (
    loading
  ) {
    return (
      <LoadingScreen />
    )
  }


  if (
    error
    || !dashboard
  ) {
    return (
      <ErrorState
        message={
          error
          ?? (
            "No dashboard data "
            + "was returned by the API."
          )
        }
        onRetry={() => {
          void loadDashboard()
        }}
      />
    )
  }


  /* =======================================================
     MAIN APPLICATION
     ======================================================= */

  return (
    <div className="min-h-screen bg-background text-foreground">

      <AppSidebar
        activeItem={
          activeItem
        }
        onSelect={
          handleNavigation
        }
      />


      <MobileNav
        activeItem={
          activeItem
        }
        onSelect={
          handleNavigation
        }
      />


      <div className="min-h-screen lg:pl-70">

        <TopBar
          pageTitle={
            PAGE_TITLES[
              activeItem
            ]
          }
        />


        <main
          className="
            citypulse-grid
            min-h-[calc(100vh-76px)]
            overflow-x-hidden
            px-3 pb-28 pt-4
            sm:px-5
            sm:pt-5
            lg:p-8
          "
        >
          <div className="mx-auto w-full max-w-[1600px]">

            {/* =============================================
                GLOBAL ACTIVE LOCATION SELECTOR
               ============================================= */}

            <LocationSelector
              locations={
                locations
              }
              activeLocationId={
                selectedLocationId
              }
              switching={
                switchingLocation
              }
              onSelect={
                handleLocationSelect
              }
            />


            {/* =============================================
                CURRENT APPLICATION MODULE
               ============================================= */}

            <ModuleContent
              activeItem={
                activeItem
              }
              dashboard={
                dashboard
              }
              locations={
                locations
              }
              selectedLocationId={
                selectedLocationId
              }
              onLocationSelect={
                handleLocationSelect
              }
            />

          </div>
        </main>
      </div>
    </div>
  )
}


/* =========================================================
   MODULE SWITCHER
   ========================================================= */

function ModuleContent({
  activeItem,
  dashboard,
  locations,
  selectedLocationId,
  onLocationSelect,
}: {
  activeItem: string
  dashboard: DashboardData

  locations:
    SupportedLocation[]

  selectedLocationId:
    number

  onLocationSelect:
    (
      locationId: number
    ) => void
}) {

  switch (
    activeItem
  ) {

    case "forecast":
      return (
        <ForecastView
          dashboard={
            dashboard
          }
        />
      )


    case "map":
      return (
        <MapView
          dashboard={
            dashboard
          }
          locations={
            locations
          }
          selectedLocationId={
            selectedLocationId
          }
          onLocationSelect={
            onLocationSelect
          }
        />
      )


    case "alerts":
      return (
        <AlertsView
          dashboard={
            dashboard
          }
        />
      )


    case "model":
      return (
        <ModelView
          dashboard={
            dashboard
          }
          supportedStationCount={
            locations.length
          }
        />
      )


    default:
      return (
        <CommandCentreView
          dashboard={
            dashboard
          }
          locations={
            locations
          }
          selectedLocationId={
            selectedLocationId
          }
          onLocationSelect={
            onLocationSelect
          }
        />
      )
  }
}


/* =========================================================
   COMMAND CENTRE
   ========================================================= */

function CommandCentreView({
  dashboard,
  locations,
  selectedLocationId,
  onLocationSelect,
}: {
  dashboard:
    DashboardData

  locations:
    SupportedLocation[]

  selectedLocationId:
    number

  onLocationSelect:
    (
      locationId: number
    ) => void
}) {

  const measuredPm25 =
    dashboard
      .measurement
      .pm25_ug_m3


  const predictedPm25 =
    dashboard
      .forecast
      .predicted_pm25_ug_m3


  return (
    <>
      <ModuleHero
        eyebrow="CityPulse Intelligence Layer"
        title="Predict Lahore's air-quality risk"
        goldText="before it becomes a crisis."
        description={`
          Monitoring, prediction and risk intelligence
          powered by location-specific Lahore PM2.5
          observations, weather information and
          machine learning.
        `}
        badgeTitle="Active Location"
        badgeValue={
          dashboard
            .station
            .name
        }
      />


      <section
        className="
          mt-5 grid gap-4
          sm:grid-cols-2
          xl:grid-cols-4
        "
      >
        <KpiCard
          title="Measured PM2.5"
          value={
            measuredPm25.toFixed(
              1
            )
          }
          unit="µg/m³"
          subtitle={
            `${dashboard.station.name} · OpenAQ`
          }
          icon={
            Wind
          }
        />


        <KpiCard
          title="Predicted PM2.5"
          value={
            predictedPm25.toFixed(
              2
            )
          }
          unit="µg/m³"
          subtitle="Station-aware Random Forest · +1 hour"
          icon={
            BrainCircuit
          }
          highlighted
        />


        <KpiCard
          title="Temperature"
          value={
            dashboard
              .measurement
              .temperature_c
              .toFixed(
                1
              )
          }
          unit="°C"
          subtitle="Open-Meteo weather feature"
          icon={
            Thermometer
          }
        />


        <KpiCard
          title="Humidity"
          value={
            dashboard
              .measurement
              .relative_humidity_pct
              .toFixed(
                0
              )
          }
          unit="%"
          subtitle="Open-Meteo weather feature"
          icon={
            Droplets
          }
        />
      </section>


      <section
        className="
          mt-5 grid gap-5
          xl:grid-cols-[1.15fr_0.85fr]
        "
      >
        <PredictionPanel
          currentPm25={
            measuredPm25
          }
          predictedPm25={
            predictedPm25
          }
          riskLevel={
            dashboard
              .risk
              .level
          }
        />


        <ForecastChart
          measuredPm25={
            measuredPm25
          }
          predictedPm25={
            predictedPm25
          }
        />
      </section>


      <section
        className="
          mt-5 grid
          items-start gap-5
          xl:grid-cols-[1.15fr_0.85fr]
        "
      >
        <LahoreMap
          locations={
            locations
          }
          activeLocationId={
            selectedLocationId
          }
          onLocationSelect={
            onLocationSelect
          }
        />


        <div className="grid gap-5">

          <RiskPanel
            predictedPm25={
              predictedPm25
            }
            level={
              dashboard
                .risk
                .level
            }
            responseStage={
              dashboard
                .risk
                .response_stage
            }
            referenceBand={
              dashboard
                .risk
                .aqi_reference_band
            }
            recommendation={
              dashboard
                .risk
                .recommendation
            }
          />


          <AlertPanel
            level={
              dashboard
                .risk
                .level
            }
            recommendation={
              dashboard
                .risk
                .recommendation
            }
          />

        </div>
      </section>


      <SystemFooter
        dashboard={
          dashboard
        }
      />
    </>
  )
}


/* =========================================================
   FORECAST INTELLIGENCE
   ========================================================= */

function ForecastView({
  dashboard,
}: {
  dashboard:
    DashboardData
}) {

  const measuredPm25 =
    dashboard
      .measurement
      .pm25_ug_m3


  const predictedPm25 =
    dashboard
      .forecast
      .predicted_pm25_ug_m3


  return (
    <>
      <ModuleHero
        eyebrow="Forecast Intelligence"
        title="AI-powered PM2.5"
        goldText="next-hour prediction."
        description={`
          Explore the latest measured observation,
          location-specific weather conditions and
          CityPulse machine-learning forecast for
          ${dashboard.station.name}.
        `}
        badgeTitle="Active Location"
        badgeValue={
          dashboard
            .station
            .name
        }
      />


      <section
        className="
          mt-5 grid gap-4
          sm:grid-cols-2
          xl:grid-cols-4
        "
      >
        <KpiCard
          title="Measured PM2.5"
          value={
            measuredPm25.toFixed(
              1
            )
          }
          unit="µg/m³"
          subtitle={
            dashboard
              .station
              .name
          }
          icon={
            Wind
          }
        />


        <KpiCard
          title="AI Forecast"
          value={
            predictedPm25.toFixed(
              2
            )
          }
          unit="µg/m³"
          subtitle="PM2.5(t + 1 hour)"
          icon={
            BrainCircuit
          }
          highlighted
        />


        <KpiCard
          title="Temperature"
          value={
            dashboard
              .measurement
              .temperature_c
              .toFixed(
                1
              )
          }
          unit="°C"
          subtitle="Location-specific weather feature"
          icon={
            Thermometer
          }
        />


        <KpiCard
          title="Humidity"
          value={
            dashboard
              .measurement
              .relative_humidity_pct
              .toFixed(
                0
              )
          }
          unit="%"
          subtitle="Location-specific weather feature"
          icon={
            Droplets
          }
        />
      </section>


      <section
        className="
          mt-5 grid gap-5
          xl:grid-cols-[1.1fr_0.9fr]
        "
      >
        <PredictionPanel
          currentPm25={
            measuredPm25
          }
          predictedPm25={
            predictedPm25
          }
          riskLevel={
            dashboard
              .risk
              .level
          }
        />


        <ForecastChart
          measuredPm25={
            measuredPm25
          }
          predictedPm25={
            predictedPm25
          }
        />
      </section>


      <section
        className="
          mt-5 grid gap-4
          md:grid-cols-4
        "
      >
        <InfoStrip
          icon={
            MapPin
          }
          title="Forecast Location"
          value={
            dashboard
              .station
              .name
          }
        />


        <InfoStrip
          icon={
            Clock3
          }
          title="Measurement Time"
          value={
            formatLahoreTime(
              dashboard
                .measurement
                .timestamp_utc
            )
          }
        />


        <InfoStrip
          icon={
            BrainCircuit
          }
          title="Forecast Valid For"
          value={
            formatLahoreTime(
              dashboard
                .forecast
                .timestamp_utc
            )
          }
        />


        <InfoStrip
          icon={
            Activity
          }
          title="Risk"
          value={
            dashboard
              .risk
              .level
          }
        />
      </section>


      <ScopeNote
        dashboard={
          dashboard
        }
      />
    </>
  )
}


/* =========================================================
   LAHORE MAP
   ========================================================= */

function MapView({
  dashboard,
  locations,
  selectedLocationId,
  onLocationSelect,
}: {
  dashboard:
    DashboardData

  locations:
    SupportedLocation[]

  selectedLocationId:
    number

  onLocationSelect:
    (
      locationId: number
    ) => void
}) {

  return (
    <>
      <ModuleHero
        eyebrow="Lahore Spatial Intelligence"
        title="Select where CityPulse"
        goldText="should generate intelligence."
        description={`
          CityPulse supports ${locations.length}
          validated Lahore OpenAQ monitoring stations.
          Select a station directly or click anywhere
          on the Lahore map to use the nearest supported
          prediction location.
        `}
        badgeTitle="Active Location"
        badgeValue={
          dashboard
            .station
            .name
        }
      />


      <section className="mt-5">
        <LahoreMap
          locations={
            locations
          }
          activeLocationId={
            selectedLocationId
          }
          onLocationSelect={
            onLocationSelect
          }
        />
      </section>


      <section
        className="
          mt-5 grid gap-4
          sm:grid-cols-2
          xl:grid-cols-4
        "
      >
        <InfoStrip
          icon={
            MapPin
          }
          title="Active Monitoring Location"
          value={
            dashboard
              .station
              .name
          }
        />


        <InfoStrip
          icon={
            Activity
          }
          title="OpenAQ Location ID"
          value={
            String(
              dashboard
                .station
                .location_id
            )
          }
        />


        <InfoStrip
          icon={
            Activity
          }
          title="Sensor ID"
          value={
            String(
              dashboard
                .station
                .sensor_id
            )
          }
        />


        <InfoStrip
          icon={
            Database
          }
          title="Provider"
          value={
            dashboard
              .station
              .provider
            ?? "OpenAQ"
          }
        />
      </section>


      <ScopeNote
        dashboard={
          dashboard
        }
      />
    </>
  )
}


/* =========================================================
   RISK ALERTS
   ========================================================= */

function AlertsView({
  dashboard,
}: {
  dashboard:
    DashboardData
}) {

  const predictedPm25 =
    dashboard
      .forecast
      .predicted_pm25_ug_m3


  return (
    <>
      <ModuleHero
        eyebrow="Urban Risk Intelligence"
        title="Convert prediction into"
        goldText="citizen action."
        description={`
          CityPulse converts the PM2.5 forecast for
          ${dashboard.station.name} into understandable
          risk intelligence, preparedness stages and
          practical citizen guidance.
        `}
        badgeTitle="Current Forecast Risk"
        badgeValue={
          dashboard
            .risk
            .level
        }
      />


      <section
        className="
          mt-5 grid
          items-start gap-5
          xl:grid-cols-2
        "
      >
        <RiskPanel
          predictedPm25={
            predictedPm25
          }
          level={
            dashboard
              .risk
              .level
          }
          responseStage={
            dashboard
              .risk
              .response_stage
          }
          referenceBand={
            dashboard
              .risk
              .aqi_reference_band
          }
          recommendation={
            dashboard
              .risk
              .recommendation
          }
        />


        <AlertPanel
          level={
            dashboard
              .risk
              .level
          }
          recommendation={
            dashboard
              .risk
              .recommendation
          }
        />
      </section>


      <section
        className="
          mt-5 grid gap-4
          sm:grid-cols-2
          xl:grid-cols-4
        "
      >
        <InfoStrip
          icon={
            MapPin
          }
          title="Active Location"
          value={
            dashboard
              .station
              .name
          }
        />


        <InfoStrip
          icon={
            ShieldAlert
          }
          title="Risk Level"
          value={
            dashboard
              .risk
              .level
          }
        />


        <InfoStrip
          icon={
            Activity
          }
          title="Response Stage"
          value={
            dashboard
              .risk
              .response_stage
          }
        />


        <InfoStrip
          icon={
            BrainCircuit
          }
          title="AQI Reference Band"
          value={
            dashboard
              .risk
              .aqi_reference_band
          }
        />
      </section>


      <ScopeNote
        dashboard={
          dashboard
        }
      />
    </>
  )
}


/* =========================================================
   DATA & MODEL
   ========================================================= */

function ModelView({
  dashboard,
  supportedStationCount,
}: {
  dashboard:
    DashboardData

  supportedStationCount:
    number
}) {

  const mae =
    dashboard
      .model_metrics
      .mae


  const rmse =
    dashboard
      .model_metrics
      .rmse


  const r2 =
    dashboard
      .model_metrics
      .r2


  return (
    <>
      <ModuleHero
        eyebrow="Data & Model Intelligence"
        title="Inside the"
        goldText="CityPulse prediction engine."
        description={`
          CityPulse uses a station-aware pooled
          Random Forest model trained from multiple
          validated Lahore monitoring locations.
        `}
        badgeTitle="Model Status"
        badgeValue="Multi-location · Deployed"
      />


      <section
        className="
          mt-5 grid gap-4
          md:grid-cols-2
          xl:grid-cols-3
        "
      >
        <InfoStrip
          icon={
            BrainCircuit
          }
          title="Prediction Model"
          value={
            dashboard
              .forecast
              .model
          }
        />


        <InfoStrip
          icon={
            Database
          }
          title="Model Type"
          value={
            dashboard
              .forecast
              .model_type
          }
        />


        <InfoStrip
          icon={
            Clock3
          }
          title="Forecast Horizon"
          value={
            `PM2.5(t + ${
              dashboard
                .forecast
                .horizon_hours
            } hour)`
          }
        />


        <InfoStrip
          icon={
            MapPin
          }
          title="Active Monitoring Location"
          value={
            dashboard
              .station
              .name
          }
        />


        <InfoStrip
          icon={
            Database
          }
          title="Supported Stations"
          value={
            `${supportedStationCount} Lahore locations`
          }
        />


        <InfoStrip
          icon={
            Activity
          }
          title="Prediction Target"
          value="Future PM2.5 concentration"
        />


        <InfoStrip
          icon={
            Database
          }
          title="Air Quality Data"
          value="OpenAQ"
        />


        <InfoStrip
          icon={
            Thermometer
          }
          title="Weather Data"
          value="Open-Meteo"
        />


        <InfoStrip
          icon={
            Activity
          }
          title="Chronological Evaluation"
          value="70% train · 15% validation · 15% test"
        />
      </section>


      {
        (
          mae !== undefined
          || rmse !== undefined
          || r2 !== undefined
        )
        && (
          <section
            className="
              mt-5 grid gap-4
              sm:grid-cols-3
            "
          >
            <MetricCard
              title="Held-out Test MAE"
              value={
                mae !== undefined
                  ? mae.toFixed(2)
                  : "—"
              }
              unit="µg/m³"
            />


            <MetricCard
              title="Held-out Test RMSE"
              value={
                rmse !== undefined
                  ? rmse.toFixed(2)
                  : "—"
              }
              unit="µg/m³"
            />


            <MetricCard
              title="Held-out Test R²"
              value={
                r2 !== undefined
                  ? r2.toFixed(3)
                  : "—"
              }
              unit=""
            />
          </section>
        )
      }


      <section
        className="
          mt-5 rounded-2xl
          p-6
          citypulse-panel
        "
      >
        <div className="citypulse-eyebrow">
          Model Methodology
        </div>


        <h2 className="mt-2 text-lg font-semibold text-white">
          Station-aware time-series PM2.5 forecasting
        </h2>


        <div
          className="
            mt-5 grid gap-4
            md:grid-cols-2
            xl:grid-cols-4
          "
        >
          <MethodCard
            number="01"
            title="Monitor"
            text={
              "PM2.5 observations from supported "
              + "OpenAQ Lahore stations combined "
              + "with Open-Meteo weather."
            }
          />


          <MethodCard
            number="02"
            title="Engineer"
            text={
              "Station-specific PM2.5 lag and rolling "
              + "features are created without using "
              + "future observations."
            }
          />


          <MethodCard
            number="03"
            title="Predict"
            text={
              "A station-aware pooled Random Forest "
              + "estimates PM2.5 concentration one "
              + "hour ahead."
            }
          />


          <MethodCard
            number="04"
            title="Act"
            text={
              "The forecast is converted into risk "
              + "classification, response stage and "
              + "citizen guidance."
            }
          />
        </div>
      </section>


      <section
        className="
          mt-5 grid gap-4
          md:grid-cols-2
        "
      >
        <InfoStrip
          icon={
            Clock3
          }
          title="Latest Observation"
          value={
            formatLahoreTime(
              dashboard
                .measurement
                .timestamp_utc
            )
          }
        />


        <InfoStrip
          icon={
            Clock3
          }
          title="Forecast Timestamp"
          value={
            formatLahoreTime(
              dashboard
                .forecast
                .timestamp_utc
            )
          }
        />
      </section>


      <ScopeNote
        dashboard={
          dashboard
        }
      />
    </>
  )
}


/* =========================================================
   SHARED UI
   ========================================================= */

function ModuleHero({
  eyebrow,
  title,
  goldText,
  description,
  badgeTitle,
  badgeValue,
}: {
  eyebrow:
    string

  title:
    string

  goldText:
    string

  description:
    string

  badgeTitle:
    string

  badgeValue:
    string
}) {

  return (
    <section
      className="
        relative
        overflow-hidden
        rounded-2xl
        p-6
        citypulse-panel-strong
        lg:p-7
      "
    >
      <div
        className="
          pointer-events-none
          absolute
          -right-20
          -top-24
          size-72
          rounded-full
          bg-primary/10
          blur-3xl
        "
      />


      <div
        className="
          relative
          flex flex-wrap
          items-start
          justify-between
          gap-5
        "
      >
        <div className="max-w-3xl">

          <Badge
            variant="outline"
            className="
              border-primary/30
              bg-primary/8
              text-primary
            "
          >
            <Activity className="mr-1.5 size-3" />

            {eyebrow}
          </Badge>


          <h2
            className="
              mt-5
              max-w-3xl
              text-2xl
              font-semibold
              tracking-[-0.035em]
              text-white
              sm:text-3xl
              lg:text-4xl
            "
          >
            {title}
            {" "}

            <span className="citypulse-gold-text">
              {goldText}
            </span>
          </h2>


          <p
            className="
              mt-4
              max-w-2xl
              whitespace-normal
              text-sm
              leading-7
              text-muted-foreground
            "
          >
            {description}
          </p>
        </div>


        <div
          className="
            max-w-xs
            rounded-xl
            border border-primary/20
            bg-primary/5
            px-4 py-3
          "
        >
          <div className="citypulse-eyebrow">
            {badgeTitle}
          </div>

          <div className="mt-1 text-xs font-medium text-primary">
            {badgeValue}
          </div>
        </div>
      </div>
    </section>
  )
}


/* =========================================================
   FOOTER INTELLIGENCE
   ========================================================= */

function SystemFooter({
  dashboard,
}: {
  dashboard:
    DashboardData
}) {

  return (
    <>
      <section
        className="
          mt-5 grid gap-4
          sm:grid-cols-2
          xl:grid-cols-4
        "
      >
        <InfoStrip
          icon={
            MapPin
          }
          title="Active Location"
          value={
            dashboard
              .station
              .name
          }
        />


        <InfoStrip
          icon={
            BrainCircuit
          }
          title="Prediction Model"
          value={
            dashboard
              .forecast
              .model
          }
        />


        <InfoStrip
          icon={
            Clock3
          }
          title="Forecast Horizon"
          value={
            `PM2.5(t + ${
              dashboard
                .forecast
                .horizon_hours
            } hour)`
          }
        />


        <InfoStrip
          icon={
            Activity
          }
          title="Risk Classification"
          value="Punjab EPA PM2.5 Bands"
        />
      </section>


      <section
        className="
          mt-5 grid gap-4
          md:grid-cols-2
        "
      >
        <InfoStrip
          icon={
            Clock3
          }
          title="Latest Measurement"
          value={
            formatLahoreTime(
              dashboard
                .measurement
                .timestamp_utc
            )
          }
        />


        <InfoStrip
          icon={
            BrainCircuit
          }
          title="Forecast Valid For"
          value={
            formatLahoreTime(
              dashboard
                .forecast
                .timestamp_utc
            )
          }
        />
      </section>


      <ScopeNote
        dashboard={
          dashboard
        }
      />
    </>
  )
}


/* =========================================================
   SCOPE NOTE
   ========================================================= */

function ScopeNote({
  dashboard,
}: {
  dashboard:
    DashboardData
}) {

  return (
    <div
      className="
        mt-5
        rounded-xl
        border border-primary/15
        bg-primary/4
        px-4 py-3
        text-[11px]
        leading-5
        text-muted-foreground
      "
    >
      {
        dashboard
          .scope_note
      }

      {" "}

      {
        dashboard
          .regulatory_note
      }
    </div>
  )
}


/* =========================================================
   INFO STRIP
   ========================================================= */

function InfoStrip({
  icon: Icon,
  title,
  value,
}: {
  icon:
    typeof Activity

  title:
    string

  value:
    string
}) {

  return (
    <div
      className="
        flex items-center gap-3
        rounded-xl
        border border-primary/15
        bg-card/70
        px-4 py-3
      "
    >
      <div className="citypulse-icon-box size-9 shrink-0">
        <Icon className="size-4" />
      </div>


      <div className="min-w-0">
        <div className="citypulse-eyebrow">
          {title}
        </div>

        <div
          className="
            mt-1
            text-xs
            font-medium
            text-white
          "
        >
          {value}
        </div>
      </div>
    </div>
  )
}


/* =========================================================
   MODEL METRIC CARD
   ========================================================= */

function MetricCard({
  title,
  value,
  unit,
}: {
  title:
    string

  value:
    string

  unit:
    string
}) {

  return (
    <div
      className="
        rounded-xl
        border border-primary/15
        bg-card/70
        p-5
      "
    >
      <div className="citypulse-eyebrow">
        {title}
      </div>


      <div className="mt-3 flex items-end gap-2">
        <span className="text-2xl font-semibold text-primary">
          {value}
        </span>

        {
          unit
          && (
            <span className="pb-1 text-xs text-muted-foreground">
              {unit}
            </span>
          )
        }
      </div>
    </div>
  )
}


/* =========================================================
   METHODOLOGY CARD
   ========================================================= */

function MethodCard({
  number,
  title,
  text,
}: {
  number:
    string

  title:
    string

  text:
    string
}) {

  return (
    <div
      className="
        rounded-xl
        border border-primary/15
        bg-primary/4
        p-4
      "
    >
      <div className="citypulse-eyebrow">
        {number}
      </div>


      <div className="mt-2 text-sm font-semibold text-white">
        {title}
      </div>


      <p className="mt-2 text-xs leading-5 text-muted-foreground">
        {text}
      </p>
    </div>
  )
}


export default App