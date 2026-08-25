import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import {
  Activity,
  TrendingUp,
} from "lucide-react"


type ForecastChartProps = {
  measuredPm25: number
  predictedPm25: number
}


export function ForecastChart({
  measuredPm25,
  predictedPm25,
}: ForecastChartProps) {
  const forecastData = [
    {
      label: "Measured",
      pm25: measuredPm25,
    },
    {
      label: "+1h Forecast",
      pm25: predictedPm25,
    },
  ]

  return (
    <section className="rounded-2xl p-6 citypulse-panel">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="size-4 text-primary" />

            <span className="citypulse-eyebrow">
              Forecast Visualization
            </span>
          </div>

          <h2 className="mt-2 text-lg font-semibold text-white">
            Observed vs Predicted PM2.5
          </h2>

          <p className="mt-1 text-xs text-muted-foreground">
            Latest available dataset observation
          </p>
        </div>

        <div
          className="
            flex items-center gap-2
            rounded-full
            border border-primary/20
            bg-primary/5
            px-3 py-1.5
            text-[11px]
            text-primary
          "
        >
          <Activity className="size-3" />
          1-hour horizon
        </div>
      </div>

      <div className="my-5 citypulse-gold-line" />

      <div className="h-72 w-full">
        <ResponsiveContainer
          width="100%"
          height="100%"
        >
          <BarChart
            data={forecastData}
            margin={{
              top: 10,
              right: 10,
              left: -15,
              bottom: 0,
            }}
          >
            <CartesianGrid
              stroke="rgba(214, 180, 88, 0.08)"
              vertical={false}
            />

            <XAxis
              dataKey="label"
              tick={{
                fill: "#96a4b8",
                fontSize: 11,
              }}
              axisLine={{
                stroke: "rgba(214, 180, 88, 0.15)",
              }}
              tickLine={false}
            />

            <YAxis
              tick={{
                fill: "#96a4b8",
                fontSize: 11,
              }}
              axisLine={false}
              tickLine={false}
              unit=" µg/m³"
            />

            <Tooltip
              cursor={{
                fill: "rgba(214, 180, 88, 0.04)",
              }}
              contentStyle={{
                background: "#091625",
                border:
                  "1px solid rgba(214, 180, 88, 0.28)",
                borderRadius: "12px",
                color: "#f8f5ec",
              }}
              labelStyle={{
                color: "#f0ca67",
              }}
              formatter={(value) => [
                `${Number(value).toFixed(2)} µg/m³`,
                "PM2.5",
              ]}
            />

            <Bar
              dataKey="pm25"
              radius={[10, 10, 3, 3]}
              maxBarSize={95}
            >
              <Cell fill="#8293aa" />
              <Cell fill="#d6b458" />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 flex flex-wrap gap-5 text-[11px] text-muted-foreground">
        <div className="flex items-center gap-2">
          <span className="size-2 rounded-full bg-[#8293aa]" />
          Measured observation
        </div>

        <div className="flex items-center gap-2">
          <span className="size-2 rounded-full bg-primary" />
          AI forecast
        </div>
      </div>
    </section>
  )
}