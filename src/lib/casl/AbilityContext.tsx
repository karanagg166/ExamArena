"use client";

import React, { useMemo } from "react";
import { AbilityProvider as CaslAbilityProvider, Can as CaslCan, useAbility as useCaslAbility } from "@casl/react";
import { useAuthStore } from "@/stores";
import { defineAbilityFor } from "./ability";
import type { AppAbility } from "./types";

export interface AbilityProviderProps {
  children: React.ReactNode;
}

/**
 * React Context Provider that reactively binds CASL abilities to the current authenticated user state.
 */
export function AbilityProvider({ children }: AbilityProviderProps) {
  const user = useAuthStore((s) => s.user);

  const ability = useMemo(() => {
    return defineAbilityFor(user);
  }, [user]);

  return (
    <CaslAbilityProvider value={ability}>
      {children}
    </CaslAbilityProvider>
  );
}

/**
 * Access the active CASL AppAbility instance anywhere in client components.
 */
export function useAbility(): AppAbility {
  return useCaslAbility<AppAbility>();
}

export const Can = CaslCan;
