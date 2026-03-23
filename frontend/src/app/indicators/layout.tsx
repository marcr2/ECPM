"use client";

import { useState, createContext, useContext, type ReactNode } from "react";
import { MethodologyToggle } from "@/components/indicators/methodology-toggle";

const METHODOLOGIES = [
  { slug: "shaikh-tonak", name: "Shaikh/Tonak" },
  { slug: "kliman", name: "Kliman TSSI" },
];

interface MethodologyContextValue {
  methodology: string;
  setMethodology: (slug: string) => void;
}

const MethodologyContext = createContext<MethodologyContextValue>({
  methodology: "shaikh-tonak",
  setMethodology: () => {},
});

export function useMethodology() {
  return useContext(MethodologyContext);
}

/**
 * Layout for the /indicators section.
 *
 * Provides a global MethodologyToggle at the top and passes
 * the active methodology to all child pages via React context.
 */
export default function IndicatorsLayout({
  children,
}: {
  children: ReactNode;
}) {
  const [methodology, setMethodology] = useState("shaikh-tonak");

  return (
    <MethodologyContext.Provider value={{ methodology, setMethodology }}>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">
              Indicators
            </h1>
            <p className="text-sm text-muted-foreground">
              Marxist economic indicators computed from NIPA data
            </p>
          </div>
          <MethodologyToggle
            active={methodology}
            onChange={setMethodology}
            methodologies={METHODOLOGIES}
          />
        </div>
        {children}
      </div>
    </MethodologyContext.Provider>
  );
}
