// Forecast page layout:
// LEFT PANEL: Configuration
//   - Symbol selector (autocomplete)
//   - Target mode (RAW_PRICE / LOG_RETURN)
//   - Model selector (TimesFM3, TimesFM2.5, baselines)
//   - Context length (slider: 32-4096, default 512)
//   - Horizon (slider: 1-128, default 5)
//   - Cutoff date picker
//   - [RUN FORECAST] button
//
// CENTER: Financial chart (ECharts)
//   - Historical candlestick/line chart
//   - Forecast overlay (point + quantile bands)
//   - Q10-Q90 shaded area
//   - Q20-Q80 darker shaded area
//   - Median line
//   - Legend: "Model Forecast Quantiles (NOT confidence intervals)"
//
// RIGHT PANEL: Forecast table
//   - Step | Point | Q10 | Q50 | Q90 | Actual | Error
//
// BOTTOM: Research disclaimer
//   - "Forecasts are research outputs, not financial advice"
