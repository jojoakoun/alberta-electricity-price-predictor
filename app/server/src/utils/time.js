const ALBERTA_TIME_ZONE = "America/Edmonton";

function formatAlbertaTime(value) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    throw new TypeError("A valid timestamp is required.");
  }

  // Return the local clock time expected by the consumer UI.
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: ALBERTA_TIME_ZONE,
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(date);
}

module.exports = {
  ALBERTA_TIME_ZONE,
  formatAlbertaTime,
};
