function dollarsPerMwhToCentsPerKwh(value) {
  const price = Number(value);

  if (!Number.isFinite(price)) {
    throw new TypeError("Price must be a finite number.");
  }

  // Preserve small positive values so the client can distinguish
  // a near-zero market price from an exact zero price.
  return Number((price / 10).toFixed(4));
}

module.exports = {
  dollarsPerMwhToCentsPerKwh,
};
