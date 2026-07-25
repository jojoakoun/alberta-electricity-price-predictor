import { getJson } from "./client";
import { validateNowApiResponse } from "./now-contract";

export function fetchNow(signal) {
  return getJson(
    "/api/v1/now",
    signal,
    validateNowApiResponse,
  );
}
