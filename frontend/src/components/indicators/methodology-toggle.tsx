"use client";

import { Button } from "@/components/ui/button";

interface MethodologyToggleProps {
  active: string;
  onChange: (slug: string) => void;
  methodologies: { slug: string; name: string }[];
}

/**
 * Global methodology selector toggle. Displays a button group where
 * each methodology gets a button, with the active one highlighted.
 *
 * Default methodologies: "Shaikh/Tonak" and "Kliman TSSI"
 */
export function MethodologyToggle({
  active,
  onChange,
  methodologies,
}: MethodologyToggleProps) {
  return (
    <div className="inline-flex items-center gap-0.5 rounded-lg border border-border bg-muted p-0.5">
      {methodologies.map((m) => (
        <Button
          key={m.slug}
          variant={active === m.slug ? "default" : "ghost"}
          size="xs"
          onClick={() => onChange(m.slug)}
          className="rounded-md"
        >
          {m.name}
        </Button>
      ))}
    </div>
  );
}
