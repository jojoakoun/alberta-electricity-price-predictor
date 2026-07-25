import { getJson } from "./client";
import { validateTodayApiResponse } from "./today-contract";

export function fetchToday(signal) {
  return getJson(
    "/api/v1/today",
    signal,
    validateTodayApiResponse,
  );
}
