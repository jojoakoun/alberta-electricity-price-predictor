import { getPublicApiErrorMessage } from "./error-contract";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function getJson(path, signal, validateResponse) {
  const response = await fetch(path, {
    headers: {
      Accept: "application/json",
    },
    signal,
  });

  if (!response.ok) {
    let message = "The request could not be completed.";

    try {
      const errorPayload = await response.json();
      message = getPublicApiErrorMessage(errorPayload) ?? message;
    } catch {
      // Keep the safe fallback when the response is not valid JSON.
    }

    throw new ApiError(message, response.status);
  }

  const responsePayload = await response.json();

  return validateResponse(responsePayload);
}
