import {
  describe,
  expect,
  test,
} from "vitest";

import { en } from "./en";
import { fr } from "./fr";

function getKeyPaths(
  value,
  prefix = "",
) {
  if (
    value === null
    || typeof value !== "object"
  ) {
    return [prefix];
  }

  return Object.keys(value).reduce(
    (paths, key) => paths.concat(
      getKeyPaths(
        value[key],
        prefix ? `${prefix}.${key}` : key,
      ),
    ),
    [],
  );
}

describe("English and French translation parity", () => {
  test("contains exactly the same translation key paths", () => {
    expect(getKeyPaths(fr).sort()).toEqual(
      getKeyPaths(en).sort(),
    );
  });
});
