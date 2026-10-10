import { formatMagnitude, formatInteger, formatPercent, formatDecimals } from "../format";

describe("format utility suite", () => {
  test("formatMagnitude correctly abbreviates large magnitudes with 2 decimals", () => {
    expect(formatMagnitude(1_400_000_000, 2)).toBe("1.40B");
    expect(formatMagnitude(1_956_413_990, 2)).toBe("1.96B");
    expect(formatMagnitude(4_982_427, 2)).toBe("4.98M");
    expect(formatMagnitude(102_800_000, 2)).toBe("102.80M");
    expect(formatMagnitude(80_729, 2)).toBe("80.73K");
    expect(formatMagnitude(1_250_000_000_000, 2)).toBe("1.25T");
  });

  test("formatMagnitude handles edge cases and null values safely", () => {
    expect(formatMagnitude(null, 2)).toBe("0.00");
    expect(formatMagnitude(undefined, 2)).toBe("0.00");
    expect(formatMagnitude(NaN, 2)).toBe("0.00");
    expect(formatMagnitude(0, 2)).toBe("0.00");
    expect(formatMagnitude(42, 2)).toBe("42.00");
  });

  test("formatPercent keeps exactly 2 decimal values", () => {
    expect(formatPercent(60.052, 2)).toBe("60.05%");
    expect(formatPercent(55.7, 2)).toBe("55.70%");
    expect(formatPercent(0, 2)).toBe("0.00%");
    expect(formatPercent(null, 2)).toBe("0.00%");
  });

  test("formatInteger formats numbers with commas", () => {
    expect(formatInteger(5665)).toBe("5,665");
    expect(formatInteger(1007)).toBe("1,007");
    expect(formatInteger(0)).toBe("0");
    expect(formatInteger(null)).toBe("0");
  });

  test("formatDecimals formats standard decimal numbers", () => {
    expect(formatDecimals(2.174, 2)).toBe("2.17");
    expect(formatDecimals(3.1, 2)).toBe("3.10");
  });
});
