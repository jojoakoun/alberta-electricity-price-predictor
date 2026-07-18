describe("PostgreSQL pool", () => {
  const originalDatabaseUrl = process.env.DATABASE_URL;

  afterEach(() => {
    jest.resetModules();

    if (originalDatabaseUrl === undefined) {
      delete process.env.DATABASE_URL;
    } else {
      process.env.DATABASE_URL = originalDatabaseUrl;
    }
  });

  test("rejects a missing database URL", () => {
    delete process.env.DATABASE_URL;
    jest.resetModules();

    const { createPool } = require("../src/db/pool");

    expect(() => createPool("")).toThrow("DATABASE_URL is required.");
  });

  test("creates a pool from an explicit connection string", async () => {
    const { createPool } = require("../src/db/pool");

    const pool = createPool(
      "postgresql://wattwise:wattwise_dev@127.0.0.1:5433/wattwise",
    );

    expect(pool.options.max).toBe(10);
    expect(pool.options.idleTimeoutMillis).toBe(30_000);
    expect(pool.options.connectionTimeoutMillis).toBe(5_000);

    await pool.end();
  });
});
