const MINIMUM_DISPLAY_PRICE_CENTS = 0.01;

/**
 * Format electricity prices without suggesting that a free or
 * near-free market price should be interpreted as an ordinary zero.
 */
export function formatElectricityPrice(value) {
  const price = Number(value);

  if (!Number.isFinite(price)) {
    throw new TypeError(
      "Electricity price must be a finite number.",
    );
  }

  if (
    price >= 0
    && price < MINIMUM_DISPLAY_PRICE_CENTS
  ) {
    return "≤0.01";
  }

  return new Intl.NumberFormat(
    undefined,
    {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    },
  ).format(price);
}
