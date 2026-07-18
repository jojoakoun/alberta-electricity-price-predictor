function dollarsPerMwhToCentsPerKwh(value) {
  const price = Number(value);

  if (!Number.isFinite(price)) {
    throw new TypeError("Price must be a finite number.");
  }

  // Convert the internal $/MWh value to the public ¢/kWh value.
  return Number((price / 10).toFixed(2));
}

module.exports = {
  dollarsPerMwhToCentsPerKwh,
};
