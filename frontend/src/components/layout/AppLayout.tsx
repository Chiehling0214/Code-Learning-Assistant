import {
  CalendarCheck2,
  ChartNoAxesColumnIncreasing,
  CircleUserRound,
  Code2,
  Braces,
  CreditCard,
  Dumbbell,
  LayoutDashboard,
  LibraryBig,
  LogOut,
  RotateCcw,
  ShieldCheck,
} from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { GenerationNotifications } from "@/components/GenerationNotifications";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";
import { useSessionStore } from "@/store/session";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Home", icon: LayoutDashboard },
  { to: "/library", label: "Library", icon: LibraryBig },
  { to: "/today", label: "Today", icon: CalendarCheck2 },
  { to: "/review", label: "Review", icon: RotateCcw },
  { to: "/practice", label: "Practice", icon: Dumbbell },
  { to: "/progress", label: "Progress", icon: ChartNoAxesColumnIncreasing },
];

const SECONDARY_ITEMS = [
  { to: "/languages", label: "Languages", icon: Braces },
  { to: "/subscription", label: "Plan & usage", icon: CreditCard },
];

const ADMIN_ITEM = { to: "/admin", label: "Content review", icon: ShieldCheck };

function Wordmark() {
  return (
    <NavLink to="/dashboard" className="flex items-center gap-2.5 font-semibold tracking-[-0.02em]">
      <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
        <Code2 className="size-4" strokeWidth={2.2} />
      </span>
      <span className="hidden text-sm leading-tight min-[380px]:inline lg:inline">
        Code Learning Assistant
      </span>
    </NavLink>
  );
}

export function AppLayout() {
  const navigate = useNavigate();
  const { signOut } = useAuth();
  const user = useSessionStore((s) => s.user);
  const items = [...NAV_ITEMS, ...(user?.isAdmin ? [ADMIN_ITEM] : [])];

  async function handleSignOut() {
    await signOut();
    navigate("/login");
  }

  const navClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
      isActive
        ? "bg-primary/10 text-primary"
        : "text-muted-foreground hover:bg-accent/70 hover:text-foreground",
    );

  return (
    <div className="min-h-screen bg-background text-foreground lg:grid lg:grid-cols-[15.5rem_minmax(0,1fr)]">
      <a
        href="#main-content"
        className="fixed -top-20 left-3 z-[100] rounded-md bg-primary px-3 py-2 text-sm text-primary-foreground focus:top-3"
      >
        Skip to content
      </a>
      <aside className="sticky top-0 hidden h-screen flex-col border-r bg-card px-4 py-5 lg:flex">
        <div className="px-2 pb-8">
          <Wordmark />
        </div>

        <nav className="space-y-1">
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink key={item.to} to={item.to} className={navClass}>
                <Icon className="size-[18px]" strokeWidth={1.8} />
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        <div className="mt-7 border-t pt-5">
          <p className="mb-2 px-3 text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground/70">
            Account
          </p>
          {SECONDARY_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink key={item.to} to={item.to} className={navClass}>
                <Icon className="size-[18px]" strokeWidth={1.8} />
                {item.label}
              </NavLink>
            );
          })}
        </div>

        <div className="mt-auto border-t pt-4">
          <NavLink
            to="/profile"
            className="flex items-center gap-3 rounded-lg px-2 py-2 transition-colors hover:bg-accent/70"
          >
            <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-secondary text-secondary-foreground">
              <CircleUserRound className="size-[18px]" strokeWidth={1.8} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-medium">
                {user?.displayName || "My profile"}
              </span>
              <span className="block truncate text-xs text-muted-foreground">{user?.email}</span>
            </span>
          </NavLink>
          <div className="mt-1 flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="min-w-0 flex-1 justify-start text-muted-foreground"
              onClick={handleSignOut}
            >
              <LogOut className="size-4" />
              Sign out
            </Button>
            <GenerationNotifications align="left" side="top" />
          </div>
        </div>
      </aside>

      <div className="min-w-0">
        <header className="sticky top-0 z-30 border-b bg-background/95 backdrop-blur lg:hidden">
          <div className="flex h-14 items-center justify-between px-4">
            <Wordmark />
            <div className="flex items-center gap-1">
              <GenerationNotifications />
              <NavLink
                to="/profile"
                aria-label="Open profile"
                className="flex size-10 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <CircleUserRound className="size-5" />
              </NavLink>
            </div>
          </div>
        </header>

        <main
          id="main-content"
          className="mx-auto w-full max-w-7xl px-4 py-7 pb-24 sm:px-6 sm:py-10 sm:pb-24 lg:px-10 lg:pb-10"
        >
          <Outlet />
        </main>

        <nav
          aria-label="Primary navigation"
          className="fixed inset-x-0 bottom-0 z-40 flex overflow-x-auto border-t bg-card px-1 pb-[max(0.35rem,env(safe-area-inset-bottom))] pt-1.5 shadow-[0_-3px_16px_rgb(29_39_55_/_0.08)] lg:hidden"
        >
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "flex min-h-14 min-w-0 flex-1 flex-col items-center justify-center gap-1 rounded-lg px-0.5 text-[0.65rem] font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    isActive ? "bg-primary/10 text-primary" : "text-muted-foreground",
                  )
                }
              >
                <Icon className="size-[18px]" strokeWidth={1.9} aria-hidden="true" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
