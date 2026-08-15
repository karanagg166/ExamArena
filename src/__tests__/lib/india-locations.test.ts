import { describe, it, expect } from "vitest";
import {
  INDIAN_STATES_AND_CITIES,
  getIndianStates,
  getCitiesForState,
} from "@/lib/india-locations";

describe("India locations utility", () => {
  it("should have all 28 states and 8 union territories defined", () => {
    const states = getIndianStates();
    expect(states.length).toBeGreaterThanOrEqual(36);
    expect(states).toContain("Maharashtra");
    expect(states).toContain("Delhi");
    expect(states).toContain("Karnataka");
    expect(states).toContain("Tamil Nadu");
    expect(states).toContain("Uttar Pradesh");
    expect(states).toContain("Gujarat");
    expect(states).toContain("Punjab");
  });

  it("should return correct cities for Maharashtra", () => {
    const cities = getCitiesForState("Maharashtra");
    expect(cities).toContain("Mumbai");
    expect(cities).toContain("Pune");
    expect(cities).toContain("Nagpur");
  });

  it("should return correct cities for Karnataka", () => {
    const cities = getCitiesForState("Karnataka");
    expect(cities).toContain("Bengaluru");
    expect(cities).toContain("Mysuru");
    expect(cities).toContain("Mangaluru");
  });

  it("should return empty array for unknown or empty state", () => {
    expect(getCitiesForState("")).toEqual([]);
    expect(getCitiesForState("Unknown State")).toEqual([]);
  });

  it("should have non-empty city lists for every registered state", () => {
    for (const [state, cities] of Object.entries(INDIAN_STATES_AND_CITIES)) {
      expect(cities.length, `State ${state} should have at least 1 city`).toBeGreaterThan(0);
    }
  });
});
