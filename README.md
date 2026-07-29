# WattWise

```{=html}
<p align="center">
```
`<img src="app/client/public/wattwise-mark.svg" alt="WattWise mark" width="96">`{=html}
```{=html}
</p>
```
WattWise is an end-to-end machine-learning application that predicts
Alberta hourly electricity pool prices and transforms market forecasts
into simple consumer guidance.

## Product

-   Current and future hourly electricity price guidance
-   Consumer-friendly recommendations:
    -   Good time
    -   Okay time
    -   Better to wait
-   Regression models for price forecasting
-   Classification models for price-risk detection
-   Controlled model evaluation and explicit production activation
-   React application powered by an Express API and Python prediction
    worker

## System flow

``` text
AESO data
  → validation and cleaning
  → feature engineering
  → regression and classification models
  → candidate evaluation
  → explicit model activation
  → prediction worker
  → PostgreSQL
  → Express API
  → React application
```

## Technology stack

Frontend: - React - Vite - JavaScript

Backend: - Node.js - Express - PostgreSQL

Machine learning: - Python - Scikit-learn - Time-series feature
engineering - Regression forecasting - Classification-based market risk
detection

## Start locally

``` bash
make install
make start
make check
```

## Security

Never commit: - `.env` files - Credentials or API keys - Production
databases - Generated model artifacts

## License

MIT
