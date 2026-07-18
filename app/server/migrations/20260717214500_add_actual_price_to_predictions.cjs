exports.up = (pgm) => {
  pgm.addColumn("predictions", {
    actual_price: {
      type: "numeric(10,2)",
      notNull: false,
    },
  });
};

exports.down = (pgm) => {
  pgm.dropColumn("predictions", "actual_price");
};
