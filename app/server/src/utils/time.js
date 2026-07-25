const ALBERTA_TIME_ZONE = "America/Edmonton";

function formatAlbertaTime(value) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    throw new TypeError("A valid timestamp is required.");
  }

  // IANA timezone conversion keeps Alberta daylight-saving changes out of the
  // client and avoids fixed-offset timestamp errors.
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
