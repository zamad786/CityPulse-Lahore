const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  "http://127.0.0.1:8000"


export type SupportedLocation = {
  location_id: number
  sensor_id: number
  name: string
  latitude: number
  longitude: number
  provider: string | null
}


export type LocationsResponse = {
  count: number
  forecast_horizon_hours: number
  locations: SupportedLocation[]
}


export type NearestStationResponse = {
  selected_point: {
    latitude: number
    longitude: number
  }

  nearest_station: SupportedLocation

  distance_km: number

  coverage_mode: string
}


export type DashboardData = {
  data_mode: string

  station: SupportedLocation

  measurement: {
    timestamp_utc: string
    pm25_ug_m3: number
    temperature_c: number
    relative_humidity_pct: number
    precipitation_mm: number
    wind_speed_m_s: number
    wind_direction_deg: number
    surface_pressure_hpa: number
  }

  forecast: {
    timestamp_utc: string
    horizon_hours: number
    predicted_pm25_ug_m3: number
    model: string
    model_type: string
  }

  risk: {
    level: string
    response_stage: string
    aqi_reference_band: string
    severity: number
    recommendation: string
  }

  model_metrics: {
    mae?: number
    rmse?: number
    r2?: number
  }

  scope_note: string
  regulatory_note: string
}


async function parseApiResponse<T>(
  response: Response
): Promise<T> {
  if (!response.ok) {
    let detail =
      `HTTP ${response.status}`

    try {
      const body =
        await response.json()

      if (body?.detail) {
        detail =
          String(body.detail)
      }
    }
    catch {
      // Keep default error text.
    }

    throw new Error(
      detail
    )
  }

  return response.json()
}


export async function fetchSupportedLocations(): Promise<LocationsResponse> {
  const response =
    await fetch(
      `${API_BASE_URL}/locations`
    )

  return parseApiResponse<
    LocationsResponse
  >(response)
}


export async function fetchDashboardData(
  locationId?: number
): Promise<DashboardData> {
  const params =
    new URLSearchParams()

  if (
    locationId !== undefined
  ) {
    params.set(
      "location_id",
      String(locationId)
    )
  }

  const query =
    params.toString()

  const url =
    query
      ? `${API_BASE_URL}/dashboard/latest?${query}`
      : `${API_BASE_URL}/dashboard/latest`

  const response =
    await fetch(url)

  return parseApiResponse<
    DashboardData
  >(response)
}


export async function fetchNearestStation(
  latitude: number,
  longitude: number
): Promise<NearestStationResponse> {
  const params =
    new URLSearchParams({
      lat:
        String(latitude),

      lon:
        String(longitude),
    })

  const response =
    await fetch(
      `${API_BASE_URL}/dashboard/nearest?${params}`
    )

  return parseApiResponse<
    NearestStationResponse
  >(response)
}


export async function checkApiHealth(): Promise<boolean> {
  try {
    const response =
      await fetch(
        `${API_BASE_URL}/health`
      )

    return response.ok
  }
  catch {
    return false
  }
}