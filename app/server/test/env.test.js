const {
  createEnv,
} = require("../src/config/env");

describe("server environment", () => {
  test("uses Railway PORT and public binding in production", () => {
    const environment = createEnv({
      NODE_ENV: "production",
      ANALYTICS_PRIVATE_KEY: "a".repeat(32),
      PORT: "3200",
      API_PORT: "8000",
      DATABASE_URL:
        "postgres://user:password@database:5432/wattwise",
    });

    expect(environment.host).toBe("0.0.0.0");
    expect(environment.port).toBe(3200);
  });

  test("keeps the local development defaults", () => {
    const environment = createEnv({
      NODE_ENV: "development",
    });

    expect(environment.host).toBe("127.0.0.1");
    expect(environment.port).toBe(8000);
    expect(environment.databaseUrl).toBe("");
  });

  test("allows an explicit host override", () => {
    const environment = createEnv({
      NODE_ENV: "production",
      ANALYTICS_PRIVATE_KEY: "a".repeat(32),
      API_HOST: "127.0.0.1",
      PORT: "3100",
      DATABASE_URL:
        "postgres://user:password@database:5432/wattwise",
    });

    expect(environment.host).toBe("127.0.0.1");
    expect(environment.port).toBe(3100);
  });

  test("rejects a missing production database URL", () => {
    expect(() => {
      createEnv({
        NODE_ENV: "production",
        ANALYTICS_PRIVATE_KEY: "a".repeat(32),
        PORT: "3000",
      });
    }).toThrow(
      "DATABASE_URL is required in production.",
    );
  });

  test("preserves database URL connection parameters", () => {
    const databaseUrl = [
      "postgres://user:password@database:5432/wattwise",
      "?sslmode=require",
    ].join("");

    const environment = createEnv({
      NODE_ENV: "production",
      ANALYTICS_PRIVATE_KEY: "a".repeat(32),
      DATABASE_URL: databaseUrl,
    });

    expect(environment.databaseUrl).toBe(databaseUrl);
  });

  test("requires a private analytics key in production", () => {
    expect(() => createEnv({
      NODE_ENV: "production",
      PORT: "8000",
      DATABASE_URL:
        "postgresql://user:password@localhost:5432/wattwise",
    })).toThrow(
      "ANALYTICS_PRIVATE_KEY must contain at least 32 characters in production.",
    );
  });

  test("accepts a valid private analytics key in production", () => {
    const environment = createEnv({
      NODE_ENV: "production",
      PORT: "8000",
      DATABASE_URL:
        "postgresql://user:password@localhost:5432/wattwise",
      ANALYTICS_PRIVATE_KEY: "a".repeat(32),
    });

    expect(environment.analyticsPrivateKey).toBe(
      "a".repeat(32),
    );
  });
});
