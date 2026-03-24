import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Concentration Analysis | ECPM",
  description: "Corporate concentration metrics and crisis indicator correlations",
};

export default function ConcentrationLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col">
      {/* Breadcrumb header */}
      <div className="border-b border-border bg-background/95 px-6 py-3 backdrop-blur">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">ECPM</span>
          <span className="text-muted-foreground">/</span>
          <span className="font-medium text-foreground">Concentration Analysis</span>
        </div>
      </div>

      {/* Page content */}
      <div className="flex-1">{children}</div>
    </div>
  );
}
