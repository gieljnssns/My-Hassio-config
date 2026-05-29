# ml_solar_forecast — Project Summary
## Overview
Machine learning based solar radiation forecasting with a data driven model and MLflow pipeline for experiment tracking and deployment.
## Architecture
- InfluxDB connector: Fetches local weather data from InfluxDB instance
- API connector: Retrieves global weather data from Open Meteo API
- Model: XGBoost based predictor for solar radiation forecasting
- Training scripts: Data preprocessing, feature engineering, model training
- MLflow pipeline: Experiment tracking, model versioning, deployment
- Config files: Data sources, model parameters, pipeline settings
## Recent Issues
- DatetimeIndex shift error in data preparation step (`AttributeError: 'DatetimeIndex' object has no attribute 'elevation'`)
- Open Meteo API downtime preventing data fetching
## Fixes
- Removed `elevation_change` — replaced by better feature `elevation_abs` (absolute solar elevation)
- Removed `wind_direction_change` — `wind_direction_10m` not requested from API; will be added
- Implemented InfluxDB fallback when API unavailable
## Setup
1. Set up MLflow pipeline for experiment tracking
2. Configure InfluxDB connector with credentials
3. Update model parameters (XGBoost hyperparameters)
4. Run training scripts to generate predictions
5. Deploy model via MLflow pipeline
## Current State
Project is improving data fetching logic and optimizing model performance. Known issues documented here.
## Notes
- Use `influxdb-meteo` or similar datasource for weather data as fallback when API unavailable
- Review MLflow pipeline configs regularly for drift detection
- Added `wind_direction_10m` to API request for wind-based feature engineering
- Wind direction is 0-360, convert to cosine for periodic representation (directional gradient from previous hour)