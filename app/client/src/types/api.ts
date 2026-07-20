import type { RecommendationLevel } from "./recommendation";

export type ConfidenceLevel = "high" | "moderate" | "low";

export type NowResponse = {
  generatedAt: string;
  confidence: ConfidenceLevel;
  stale: boolean;

  price: {
    value: number;
    unit: "¢/kWh";
  };

  recommendation: {
    level: Exclude<RecommendationLevel, "unavailable">;
    explanationKey:
      | "lower_than_usual"
      | "acceptable_market_risk"
      | "higher_than_usual";
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

export type ApiErrorResponse = {
  error:
    | string
    | {
        code: string;
        message: string;
      };
};
