import type { NowResponse } from "../types/api";
import { getJson } from "./client";

export function fetchNow(signal?: AbortSignal): Promise<NowResponse> {
  return getJson<NowResponse>("/api/v1/now", signal);
}
