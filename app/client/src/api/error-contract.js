export function getPublicApiErrorMessage(payload) {
  if (payload === null || typeof payload !== "object") {
    return null;
  }

  if (typeof payload.error === "string" && payload.error.trim() !== "") {
    return payload.error;
  }

  if (
    payload.error !== null
    && typeof payload.error === "object"
    && typeof payload.error.message === "string"
    && payload.error.message.trim() !== ""
  ) {
    return payload.error.message;
  }

  return null;
}
