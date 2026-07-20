import type { TodayResponse } from "../types/api";
import { getJson } from "./client";

export function fetchToday(
  signal?: AbortSignal,
): Promise<TodayResponse> {
  return getJson<TodayResponse>("/api/v1/today", signal);
}
