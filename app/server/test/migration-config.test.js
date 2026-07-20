const packageJson = require("../package.json");

describe("production migration configuration", () => {
  test("runs production migrations from DATABASE_URL", () => {
    expect(
      packageJson.scripts["migrate:prod"],
    ).toBe(
      "node-pg-migrate up --migrations-dir migrations",
    );

    expect(
      packageJson.scripts["migrate:prod"],
    ).not.toContain("dotenv");
  });

  test("provides an explicit production rollback command", () => {
    expect(
      packageJson.scripts["migrate:prod:down"],
    ).toBe(
      "node-pg-migrate down --migrations-dir migrations",
    );
  });
});
