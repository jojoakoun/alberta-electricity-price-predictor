import type { ApiErrorResponse } from "../types/api";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function getErrorMessage(payload: ApiErrorResponse): string {
  if (typeof payload.error === "string") {
    return payload.error;
  }

  return payload.error.message;
}

export async function getJson<TResponse>(
  path: string,
  signal?: AbortSignal,
): Promise<TResponse> {
  const response = await fetch(path, {
    headers: {
      Accept: "application/json",
    },
    signal,
  });

  if (!response.ok) {
    let message = "The request could not be completed.";

    try {
      const payload = (await response.json()) as ApiErrorResponse;
      message = getErrorMessage(payload);
    } catch {
      // Keep the safe fallback when the response is not valid JSON.
    }

    throw new ApiError(message, response.status);
  }

  return response.json() as Promise<TResponse>;
}
