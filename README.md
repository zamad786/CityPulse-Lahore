# 🌆 CityPulse Lahore

### AI-Powered Air Quality Prediction & Urban Risk Intelligence Platform

**Smart City Hackathon Lahore — Theme 2: City Intelligence**

> **Predicting Problems Before They Happen, Not After.**

CityPulse Lahore is a predictive smart-city platform that forecasts **PM2.5 air pollution one hour ahead** and converts the prediction into useful **urban risk intelligence, preparedness guidance, and citizen recommendations**.

The core workflow is:

**Monitoring → Prediction → Risk Intelligence → Action**

---

## 🎯 Problem

Most air-quality dashboards are reactive: they show what pollution is happening now.

CityPulse Lahore focuses on prediction:

> **What is likely to happen next, where is the risk, and what should citizens do?**

The platform combines real air-quality observations, weather information, machine learning, spatial intelligence, and risk classification into one Smart City Command Centre.

---

## ✨ Key Features

- Real PM2.5 observations from **OpenAQ**
- Weather data from **Open-Meteo**
- **19 supported Lahore monitoring locations**
- PM2.5 prediction **1 hour ahead**
- Station-aware machine-learning model
- Interactive Lahore map
- Location-based prediction switching
- Nearest-supported-station selection
- Risk classification
- Citizen recommendations
- FastAPI backend
- React + TypeScript frontend
- Responsive Smart City Command Centre UI
- 5km Radius coverage area
- Compact cloud-deployable ML model

---

## 📍 Supported Lahore Locations

CityPulse currently supports 8 OpenAQ monitoring locations:

| Location | OpenAQ Location ID |
|---|---:|
| Barki, Lahore | 4515157 |
| Civil Secretariat | 4527035 |
| Learning Alliance International, DHA | 4527173 |
| Ravi Road | 4555745 |
| Model Town | 4568423 |
| Kahna Hospital | 4609353 |
| Gulberg III | 4618814 |
| Forman Christian College & Chartered University | 4757305 |

Users can select any supported monitoring station from the dashboard.

If a user clicks an arbitrary location on the Lahore map, CityPulse identifies the **nearest supported monitoring station** and uses that station for prediction.

---

## 🤖 Machine Learning Objective

The prediction target is:

```text
PM2.5(t + 1 hour)
```

CityPulse predicts future PM2.5 concentration one hour after the latest available observation.

---

## 📊 Data Sources

### Air Quality
**OpenAQ**

Used for PM2.5 monitoring observations.

https://openaq.org/

### Weather
**Open-Meteo**

Used for hourly weather features such as:

- Temperature
- Relative humidity
- Precipitation
- Wind speed
- Wind direction
- Surface pressure

https://open-meteo.com/

### Mapping

- OpenStreetMap
- React Leaflet
- Leaflet

---

## 🧠 Feature Engineering

CityPulse uses environmental, temporal, and historical PM2.5 features.

### PM2.5 Lag Features

- 1 hour
- 2 hours
- 3 hours
- 6 hours
- 12 hours
- 24 hours

### Rolling PM2.5 Features

- 3-hour mean
- 6-hour mean
- 12-hour mean
- 24-hour mean

### Time Features

- Hour
- Day of week
- Month
- Weekend indicator

### Weather Features

- Temperature
- Relative humidity
- Precipitation
- Wind speed
- Wind direction
- Surface pressure

Lag and rolling features are calculated independently for each monitoring station.

Future observations are never used to create historical features, preventing **time-series data leakage**.

---

## 🧪 Machine Learning Methodology

Because this is time-series data, CityPulse uses a **chronological split** instead of random shuffling:

```text
70% Training
15% Validation
15% Testing
```

Earlier observations are used for training and later observations are used for validation and testing.

Models evaluated during development included:

- Linear Regression
- Random Forest Regressor
- Gradient Boosting Regressor
- XGBoost

Random Forest was selected because it provided a strong combination of:

- Predictive performance
- Stability
- Inference speed
- Simplicity
- Deployment suitability

---

## 🚀 Final Deployment Model

The final production model is a:

**Compact Station-Aware Random Forest Regressor**

Configuration:

```text
Trees: 40
Maximum Depth: 14
Minimum Samples per Leaf: 2
Maximum Features: 0.8
Forecast Horizon: +1 Hour
```

### Final Multi-Location Dataset

```text
54,727 ML samples
8 Lahore monitoring stations
31 features
1-hour forecast horizon
```

### Held-Out Test Performance

| Metric | Result |
|---|---:|
| MAE | **6.9526 µg/m³** |
| RMSE | **11.4059 µg/m³** |
| R² | **0.7872** |

---

## ⚡ Deployment Optimization

The original full multi-location Random Forest model was approximately:

```text
620.37 MB
```

The optimized deployment model is only:

```text
4.07 MB
```

This reduced the model size by more than **150×** while maintaining very similar predictive performance.

---

## Live Demo:
https://city-ai-pulse-lahore.vercel.app/

Backend API:
https://citypulse-lahore-api.vercel.app/api

API Health:
https://citypulse-lahore-api.vercel.app/api/health


## 🏗️ System Architecture

```text
OpenAQ PM2.5
      +
Open-Meteo Weather
      ↓
Data Cleaning & Validation
      ↓
Station-Specific Feature Engineering
      ↓
Compact Station-Aware Random Forest
      ↓
PM2.5 +1 Hour Prediction
      ↓
Risk Classification
      ↓
Citizen Recommendation
      ↓
FastAPI Backend
      ↓
React Smart City Dashboard
```

---

## 🖥️ Dashboard Modules

### Smart City Command Centre

Displays:

- Measured PM2.5
- Predicted PM2.5
- Temperature
- Humidity
- Risk level
- Forecast visualization
- Lahore map
- Citizen recommendation

### Forecast Intelligence

Displays location-specific current conditions and one-hour PM2.5 prediction.

### Lahore Spatial Intelligence

Allows users to:

- View supported monitoring stations
- Select a station
- Click anywhere on the Lahore map
- Find the nearest supported monitoring station

### Urban Risk Alerts

Converts the PM2.5 forecast into:

- Risk level
- Response stage
- PM2.5 reference band
- Citizen recommendation

### Data & Model Intelligence

Displays:

- Prediction model
- Data sources
- Forecast horizon
- Supported locations
- Model metrics
- Methodology

---

## ⚠️ Important Interpretation

CityPulse distinguishes between:

### Measured Data

Actual PM2.5 observations obtained from OpenAQ monitoring stations.

### Predicted Data

Machine-learning estimates of PM2.5 concentration one hour into the future.

### Risk Intelligence

Decision-support information derived from the predicted PM2.5 concentration.

CityPulse does **not** claim that its risk classification is an official government AQI declaration.

---

## 🗺️ Geographic Coverage

CityPulse provides station-specific forecasting for supported Lahore monitoring locations.

When a user clicks an arbitrary point on the map, the system uses the **nearest supported monitoring station**.

It does not claim that a pollution sensor exists at the exact clicked coordinate.

---

## 🛠️ Technology Stack

### Machine Learning

- Python
- pandas
- NumPy
- scikit-learn
- XGBoost
- joblib

### Backend

- FastAPI
- Uvicorn
- Pydantic

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- Lucide Icons
- Recharts
- React Leaflet
- OpenStreetMap

---

## 📁 Project Structure

```text
CityPulse-Lahore/
│
├── backend/
│   ├── main.py
│   ├── dashboard_router.py
│   ├── model_service.py
│   ├── risk.py
│   └── schemas.py
│
├── data/
│   └── processed/
│       ├── citypulse_multilocation_latest_features.csv
│       └── lahore_multilocation_station_candidates.csv
│
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
│
├── models/
│   └── citypulse_multilocation_model.joblib
│
├── notebooks/
├── reports/
├── screenshots/
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🔌 Backend API

### Health Check

```http
GET /health
```

### Supported Locations

```http
GET /locations
```

### Latest Location Intelligence

```http
GET /dashboard/latest?location_id=4618814
```

### Nearest Supported Station

```http
GET /dashboard/nearest?lat=31.4697&lon=74.2728
```

### Prediction Endpoint

```http
POST /predict
```

FastAPI documentation is available locally at:

```text
http://127.0.0.1:8000/docs
```

---

## ▶️ Run Locally

### 1. Create Python Environment

```powershell
python -m venv .venv
```

Activate:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Install Backend Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Start FastAPI

From the project root:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

---

## 🌐 Run Frontend

Open another terminal:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Create:

```text
frontend/.env
```

with:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Then run:

```powershell
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

## ✅ Production Build

```powershell
cd frontend
npm run build
```

Expected:

```text
✓ built in ...
```

---

## 🧪 Final Validation

Run:

```powershell
python notebooks/34_multilocation_final_validation.py
```

Expected:

```text
HEALTH ENDPOINT                     PASS
LOCATIONS ENDPOINT                  PASS
SUPPORTED STATION COUNT             PASS
STATION METADATA                    PASS
ALL 8 LOCATION DASHBOARDS           PASS
LOCATION-SPECIFIC PREDICTIONS       PASS
NEAREST-STATION LOOKUP              PASS
MODEL METRICS EXPOSED               PASS

MULTI-LOCATION FINAL QA: PASS
```

---

## 🚧 Current Limitations

- Forecast horizon is currently limited to 1 hour
- Predictions are limited to supported monitoring stations
- Arbitrary map locations use the nearest supported station
- No street-level pollution interpolation is currently performed
- Dashboard data represents the latest prepared dataset observation and should not be interpreted as a continuously live sensor feed
- Risk bands are decision-support intelligence, not official regulatory AQI
- Prediction performance varies between monitoring stations

---

## 🔮 Future Improvements

Future versions could include:

- Automated real-time OpenAQ ingestion
- Multi-hour forecasting
- Additional Lahore monitoring stations
- Prediction uncertainty intervals
- Traffic and mobility features
- Meteorological forecast integration
- Automated pollution alerts
- Historical city intelligence reporting
- Spatial interpolation when sufficient sensor density is available

---

## 🏆 Hackathon Value Proposition

Traditional dashboards answer:

> **What is happening now?**

CityPulse Lahore answers:

> **What is likely to happen next, where is the risk, and what should people do?**

This transforms air-quality monitoring into a predictive **urban intelligence system**.

---

## ✅ Project Status

- [x] Real OpenAQ air-quality data
- [x] Real Open-Meteo weather data
- [x] Data validation
- [x] Multi-location dataset
- [x] Leakage-safe feature engineering
- [x] Chronological ML evaluation
- [x] Model comparison
- [x] 1-hour PM2.5 forecasting
- [x] Compact deployment model
- [x] FastAPI backend
- [x] React frontend
- [x] Interactive Lahore map
- [x] Multi-location prediction
- [x] Risk intelligence
- [x] Citizen recommendations
- [x] Production frontend build
- [x] Automated final QA
- [ ] Public backend deployment
- [ ] Public frontend deployment

---

# CityPulse Lahore

### Monitoring → Prediction → Risk Intelligence → Action

Built for the **Smart City Hackathon Lahore — Theme 2: City Intelligence**.
