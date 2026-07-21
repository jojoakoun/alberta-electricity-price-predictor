import { getJson } from "./client";
import { validateNowApiResponse } from "./contracts";

export function fetchNow(signal) {
  return getJson(
    "/api/v1/now",
    signal,
    validateNowApiResponse,
  );
}
