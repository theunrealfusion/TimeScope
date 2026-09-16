import { z } from "zod";

// ---- Forecast ----
export const ForecastRequestSchema = z.object({
  symbol: z.string().min(1),
  model_name: z.string().default("timesfm3"),
  target_mode: z.enum(["raw_price", "log_return"]).default("raw_price"),
  context_length: z.number().int().min(32).max(4096).default(512),
  horizon: z.number().int().min(1).max(128).default(5),
  cutoff_date: z.string().datetime().optional(),
  target_variates: z.array(z.string()).default(["close"]),
});

export const ForecastResponseSchema = z.object({
  run_id: z.string(),
  symbol: z.string(),
  model_name: z.string(),
  model_version: z.string(),
  device: z.string(),
  target_mode: z.string(),
  horizon: z.number(),
  context_length: z.number(),
  origin_timestamp: z.string(),
  point_forecast: z.array(z.number()),
  forecast_prices: z.array(z.number()).nullable(),
  quantiles: z.record(z.array(z.number())).nullable(),
  reconstruction_method: z.string().nullable(),
});

export type ForecastRequest = z.infer<typeof ForecastRequestSchema>;
export type ForecastResponse = z.infer<typeof ForecastResponseSchema>;

// ---- Metrics ----
export const MetricsSchema = z.object({
  mae: z.number(),
  rmse: z.number(),
  mape: z.number(),
  smape: z.number(),
  directional_accuracy: z.number().optional(),
});

// ---- Model Info ----
export const ModelInfoSchema = z.object({
  name: z.string(),
  version: z.string(),
  provider: z.string(),
  license: z.string().nullable(),
  loaded: z.boolean(),
  device: z.string().nullable(),
  capabilities: z.array(z.string()),
});
