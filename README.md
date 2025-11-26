# Life Expectancy Prediction (ML Summative)

## [Watch Live Demo Video]

https://youtu.be/AIB4BZDZfPE

This predicts country-level life expectancy from public health and socio-economic mix features.

The mission is to build a simple predictive program that estimates country-level life expectancy using public health and socio-economic data. The tool will help governments and other stakeholders understand which factors limit longevity and show where targeted action can raise life expectancy.

- Trained Random Forest model deployed as a public FastAPI endpoint.
- Helps analysts and students explore relationships between country features and life expectancy.

**Dataset**

- Source:

## Kaggle

    https://www.kaggle.com/datasets/lashagoch/life-expectancy-who-updated

included in the repository at `linear_regression/Life-Expectancy-Data-Updated.csv` (preprocessing and feature engineering performed in `linear_regression/multivariate.ipynb`).

- Preprocessed CSV: `linear_regression/preprocessed_life_expectancy.csv` (saved by the notebook).
- Samples: preprocessed dataset included with the notebook outputs in the repo.

**Best Model**

- Random Forest Regressor → `API/models/random_forest.joblib`
- Model metadata and selected features: `API/model_selection_info.json`

**Public API**

- Base URL: `https://ml-summative.web.app/api/predict`
- Swagger UI: `https://ml-summative.web.app/api/predict/api/docs`
- Notes: no auth required • CORS enabled • request validation via Pydantic

Endpoints

- POST `/api/predict` — Accepts a JSON object with feature names matching the selected feature list and returns a prediction JSON:

## To run the Flutter App

git clone https://github.com/vmugabo/Summative.git
cd Summative
flutter pub get
flutter run -d <Device Name>
