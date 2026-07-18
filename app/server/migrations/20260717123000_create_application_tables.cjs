exports.up = (pgm) => {
  pgm.createTable("hourly_prices", {
    datetime_utc: {
      type: "timestamptz",
      primaryKey: true,
    },
    actual_price: {
      type: "numeric(10,2)",
    },
    forecast_price: {
      type: "numeric(10,2)",
    },
    alberta_internal_load: {
      type: "numeric(12,2)",
    },
    source: {
      type: "text",
      notNull: true,
    },
    inserted_at: {
      type: "timestamptz",
      notNull: true,
      default: pgm.func("now()"),
    },
  });

  pgm.createTable("prediction_runs", {
    id: {
      type: "bigserial",
      primaryKey: true,
    },
    generated_at: {
      type: "timestamptz",
      notNull: true,
    },
    status: {
      type: "text",
      notNull: true,
    },
    confidence: {
      type: "text",
    },
    spike_threshold: {
      type: "numeric(10,2)",
    },
    detail: {
      type: "text",
    },
    created_at: {
      type: "timestamptz",
      notNull: true,
      default: pgm.func("now()"),
    },
  });

  pgm.createTable("predictions", {
    id: {
      type: "bigserial",
      primaryKey: true,
    },
    prediction_run_id: {
      type: "bigint",
      notNull: true,
      references: "prediction_runs",
      onDelete: "CASCADE",
    },
    horizon_hours: {
      type: "integer",
      notNull: true,
    },
    target_time_utc: {
      type: "timestamptz",
      notNull: true,
    },
    predicted_price: {
      type: "numeric(10,2)",
      notNull: true,
    },
    spike_probability: {
      type: "numeric(8,6)",
    },
    spike_prediction: {
      type: "boolean",
    },
    recommendation: {
      type: "text",
    },
    explanation: {
      type: "text",
    },
    created_at: {
      type: "timestamptz",
      notNull: true,
      default: pgm.func("now()"),
    },
  });

  pgm.addConstraint(
    "predictions",
    "predictions_run_horizon_unique",
    {
      unique: ["prediction_run_id", "horizon_hours"],
    },
  );
};

exports.down = (pgm) => {
  pgm.dropTable("predictions");
  pgm.dropTable("prediction_runs");
  pgm.dropTable("hourly_prices");
};
