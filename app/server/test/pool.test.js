const { pool } = require("../src/db/pool");

describe("PostgreSQL pool", () => {
  test("creates one shared pool", () => {
    expect(pool).toBeDefined();
    expect(pool.options.max).toBe(10);
    expect(pool.options.idleTimeoutMillis).toBe(30_000);
    expect(pool.options.connectionTimeoutMillis).toBe(5_000);
  });

  afterAll(async () => {
    await pool.end();
  });
});
