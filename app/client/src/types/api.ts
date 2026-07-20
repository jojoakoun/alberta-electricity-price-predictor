import type { RecommendationLevel } from "./recommendation";

export type ConfidenceLevel = "high" | "moderate" | "low";

export type PublicRecommendation = Exclude<
  RecommendationLevel,
  "unavailable"
>;

export type ExplanationKey =
  | "lower_than_usual"
  | "acceptable_market_risk"
  | "higher_than_usual";

export type TemporalWordingKey =
  | "very_soon"
  | "in_a_few_hours"
  | "this_afternoon"
  | "this_evening"
  | "overnight"
  | "later_today"
  | "tomorrow_around_this_time";

export type NowResponse = {
  generatedAt: string;
  confidence: ConfidenceLevel;
  stale: boolean;

  price: {
    value: number;
    unit: "¢/kWh";
    observedAtUtc?: string;
  };

  recommendation: {
    level: PublicRecommendation;
    explanationKey: ExplanationKey;
    actionKey:
      | "run_heavy_appliances"
      | "use_if_needed"
      | "wait_if_possible";
  };

  contextKey:
    | "lower_than_usual"
    | "about_average"
    | "higher_than_usual";
};

export type TodayForecast = {
  horizonHours: 1 | 3 | 6 | 12 | 24;
  targetTimeUtc: string;
  targetTimeLocal: string;
  temporalWordingKey: TemporalWordingKey;
  priceCents: number;
  recommendation: PublicRecommendation;
  explanationKey: ExplanationKey;
};

export type TodayBestTime = {
  horizonHours: TodayForecast["horizonHours"];
  targetTimeUtc: string;
  targetTimeLocal: string;
  priceCents: number;
  recommendation: PublicRecommendation;
};

export type TodayResponse = {
  generatedAt: string;
  confidence: ConfidenceLevel;
  stale: boolean;
  forecasts: TodayForecast[];
  bestTime: TodayBestTime;
};

export type ApiErrorResponse = {
  error:
    | string
    | {
        code: string;
        message: string;
      };
};
