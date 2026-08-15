"use client";

import React, { useMemo } from "react";
import { getIndianStates, getCitiesForState } from "@/lib/india-locations";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Input } from "@/components/ui/input";

export interface IndiaStateCitySelectProps {
  selectedState: string;
  selectedCity: string;
  onStateChange: (state: string) => void;
  onCityChange: (city: string) => void;
  disabled?: boolean;
  required?: boolean;
  stateError?: string;
  cityError?: string;
  stateLabel?: string;
  cityLabel?: string;
  stateId?: string;
  cityId?: string;
  className?: string;
  stateClassName?: string;
  cityClassName?: string;
}

export function IndiaStateCitySelect({
  selectedState,
  selectedCity,
  onStateChange,
  onCityChange,
  disabled = false,
  required = false,
  stateError,
  cityError,
  stateLabel = "State",
  cityLabel = "City",
  stateId = "state-select",
  cityId = "city-select",
  className = "grid grid-cols-1 sm:grid-cols-2 gap-4",
  stateClassName,
  cityClassName,
}: IndiaStateCitySelectProps) {
  const states = useMemo(() => getIndianStates(), []);
  const cities = useMemo(
    () => (selectedState ? getCitiesForState(selectedState) : []),
    [selectedState],
  );

  const handleStateChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newState = e.target.value;
    onStateChange(newState);
    // When state changes, reset city or check if current city is in the new state's cities
    const newCities = getCitiesForState(newState);
    if (!newCities.includes(selectedCity)) {
      onCityChange("");
    }
  };

  const isCustomCity =
    Boolean(selectedCity) && cities.length > 0 && !cities.includes(selectedCity);

  return (
    <div className={className}>
      {/* State Field */}
      <div className="space-y-1.5">
        <Label htmlFor={stateId} className="text-sm font-medium">
          {stateLabel} {required && <span className="text-red-400">*</span>}
        </Label>
        <Select
          id={stateId}
          value={selectedState || ""}
          onChange={handleStateChange}
          disabled={disabled}
          className={`w-full ${stateError ? "border-red-500 ring-1 ring-red-500/20" : ""} ${stateClassName || ""}`}
        >
          <option value="" disabled>
            Select State / UT...
          </option>
          {states.map((st) => (
            <option key={st} value={st}>
              {st}
            </option>
          ))}
        </Select>
        {stateError && (
          <p className="text-xs text-red-500 mt-1">{stateError}</p>
        )}
      </div>

      {/* City Field */}
      <div className="space-y-1.5">
        <Label htmlFor={cityId} className="text-sm font-medium">
          {cityLabel} {required && <span className="text-red-400">*</span>}
        </Label>

        {cities.length > 0 && !isCustomCity ? (
          <Select
            id={cityId}
            value={selectedCity || ""}
            onChange={(e) => {
              if (e.target.value === "__OTHER__") {
                onCityChange("");
              } else {
                onCityChange(e.target.value);
              }
            }}
            disabled={disabled || !selectedState}
            className={`w-full ${cityError ? "border-red-500 ring-1 ring-red-500/20" : ""} ${cityClassName || ""}`}
          >
            <option value="" disabled>
              {selectedState ? "Select City..." : "Select State first"}
            </option>
            {cities.map((ct) => (
              <option key={ct} value={ct}>
                {ct}
              </option>
            ))}
            <option value="__OTHER__">+ Enter other city...</option>
          </Select>
        ) : (
          <div className="space-y-1">
            <Input
              id={cityId}
              placeholder={
                selectedState
                  ? "Enter your city/town name"
                  : "Select State first"
              }
              value={selectedCity || ""}
              onChange={(e) => onCityChange(e.target.value)}
              disabled={disabled || !selectedState}
              className={`w-full ${cityError ? "border-red-500 ring-1 ring-red-500/20" : ""} ${cityClassName || ""}`}
            />
            {cities.length > 0 && (
              <button
                type="button"
                onClick={() => onCityChange(cities[0] || "")}
                className="text-xs text-indigo-400 hover:text-indigo-300 underline"
              >
                Choose from state list
              </button>
            )}
          </div>
        )}

        {cityError && <p className="text-xs text-red-500 mt-1">{cityError}</p>}
      </div>
    </div>
  );
}
