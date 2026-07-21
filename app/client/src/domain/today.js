/**
 * Return whether the API proved a lower-price planning opportunity.
 *
 * The server owns the comparison. The browser only renders its result and
 * must not independently select a forecast or infer savings.
 */
export function isLowerPriceOpportunity(comparison) {
  return comparison === "forecast_lower";
}
