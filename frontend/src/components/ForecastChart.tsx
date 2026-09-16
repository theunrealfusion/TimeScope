import React from "react";
import ReactECharts from "echarts-for-react";
import type { ForecastResponse } from "../api/types";

interface ForecastChartProps {
  historicalData: { timestamp: string; close: number }[];
  forecast: ForecastResponse | null;
  targetMode: "raw_price" | "log_return";
}

export const ForecastChart: React.FC<ForecastChartProps> = ({
  historicalData,
  forecast,
  targetMode,
}) => {
  const option = {
    title: {
      text: forecast
        ? `${forecast.symbol} — ${forecast.model_name} Forecast`
        : "Select symbol and run forecast",
      subtext: "Research output only — not financial advice",
    },
    tooltip: { trigger: "axis" },
    legend: {
      data: ["Actual", "Forecast", "Q10-Q90 Band", "Q20-Q80 Band"],
    },
    xAxis: { type: "category", data: [] /* timestamps */ },
    yAxis: { type: "value", scale: true },
    series: [
      // Historical line
      {
        name: "Actual",
        type: "line",
        data: historicalData.map((d) => d.close),
        lineStyle: { width: 1.5 },
      },
      // Forecast points
      ...(forecast
        ? [
            {
              name: "Forecast",
              type: "line",
              data: forecast.point_forecast,
              lineStyle: { type: "dashed", width: 2 },
              itemStyle: { color: "#e74c3c" },
            },
          ]
        : []),
      // Quantile bands (Q10-Q90 area)
      ...(forecast?.quantiles
        ? [
            {
              name: "Model Forecast Quantiles",
              type: "line",
              data: forecast.quantiles.q10,
              areaStyle: { opacity: 0.1 },
              lineStyle: { opacity: 0 },
              stack: "quantile-lower",
            },
          ]
        : []),
    ],
  };

  return <ReactECharts option={option} style={{ height: 500 }} />;
};
