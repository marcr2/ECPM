"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  Database,
  BarChart3,
  TrendingUp,
  GitBranch,
  PieChart,
  ChevronDown,
} from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { INDICATOR_DEFS } from "@/lib/indicator-defs";

const phases = [
  {
    name: "Data Overview",
    href: "/data",
    icon: Database,
    phase: 1,
    enabled: true,
  },
  {
    name: "Indicators",
    href: "/indicators",
    icon: BarChart3,
    phase: 2,
    enabled: true,
  },
  {
    name: "Forecasting",
    href: "/forecasting",
    icon: TrendingUp,
    phase: 3,
    enabled: true,
  },
  {
    name: "Structural Analysis",
    href: "/structural",
    icon: GitBranch,
    phase: 4,
    enabled: true,
  },
  {
    name: "Concentration",
    href: "/concentration",
    icon: PieChart,
    phase: 5,
    enabled: false,
  },
];

/** Sub-links for the Indicators section */
const indicatorSubLinks = [
  { name: "Overview", href: "/indicators" },
  ...INDICATOR_DEFS.map((d) => ({
    name: d.name,
    href: `/indicators/${d.slug}`,
  })),
  { name: "Methodology", href: "/indicators/methodology" },
  { name: "Compare", href: "/indicators/compare" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-[240px] shrink-0 flex-col border-r border-border bg-sidebar text-sidebar-foreground">
      {/* Logo / Title */}
      <div className="flex h-14 items-center px-4">
        <Link href="/data" className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded bg-primary text-primary-foreground text-xs font-bold">
            EC
          </div>
          <div>
            <span className="text-sm font-semibold tracking-tight">ECPM</span>
            <span className="ml-1.5 text-[10px] text-muted-foreground">
              v0.1
            </span>
          </div>
        </Link>
      </div>

      <Separator />

      {/* Navigation */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-2 py-3">
        <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Modules
        </p>
        {phases.map((phase) => {
          const isActive =
            phase.enabled &&
            (pathname === phase.href || pathname?.startsWith(phase.href + "/"));
          const Icon = phase.icon;
          const isIndicators = phase.href === "/indicators";
          const showSubNav = isIndicators && isActive;

          if (!phase.enabled) {
            return (
              <div
                key={phase.href}
                className="flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm text-muted-foreground/50 cursor-not-allowed select-none"
              >
                <Icon className="h-4 w-4" />
                <span>{phase.name}</span>
                <span className="ml-auto text-[9px] font-medium opacity-50">
                  P{phase.phase}
                </span>
              </div>
            );
          }

          return (
            <div key={phase.href}>
              <Link
                href={phase.href}
                className={cn(
                  "flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                    : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{phase.name}</span>
                {isIndicators ? (
                  <ChevronDown
                    className={cn(
                      "ml-auto h-3.5 w-3.5 text-muted-foreground transition-transform",
                      showSubNav && "rotate-180"
                    )}
                  />
                ) : (
                  <span className="ml-auto text-[9px] font-medium text-muted-foreground">
                    P{phase.phase}
                  </span>
                )}
              </Link>

              {/* Collapsible sub-navigation for Indicators */}
              {showSubNav && (
                <div className="ml-4 mt-0.5 space-y-0.5 border-l border-border pl-2">
                  {indicatorSubLinks.map((sub) => {
                    const isSubActive = pathname === sub.href;
                    return (
                      <Link
                        key={sub.href}
                        href={sub.href}
                        className={cn(
                          "block rounded-md px-2 py-1 text-xs transition-colors",
                          isSubActive
                            ? "bg-sidebar-accent/60 text-sidebar-accent-foreground font-medium"
                            : "text-muted-foreground hover:bg-sidebar-accent/30 hover:text-sidebar-foreground"
                        )}
                      >
                        {sub.name}
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      <Separator />

      {/* Footer */}
      <div className="px-4 py-3">
        <p className="text-[10px] text-muted-foreground">
          Economic Crisis Prediction Model
        </p>
        <p className="text-[10px] text-muted-foreground/60">
          Marxist Political Economy
        </p>
      </div>
    </aside>
  );
}
