import {
  CalendarCheck2,
  ChartNoAxesColumnIncreasing,
  CircleUserRound,
  Code2,
  Braces,
  CreditCard,
  Dumbbell,
  LayoutDashboard,
  LogOut,
  RotateCcw,
  ShieldCheck,
} from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";
import { useSessionStore } from "@/store/session";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Home", icon: LayoutDashboard },
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
      <span className="text-sm leading-tight">Code Learning Assistant</span>
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
          <Button variant="ghost" size="sm" className="mt-1 w-full justify-start text-muted-foreground" onClick={handleSignOut}>
            <LogOut className="size-4" />
            Sign out
          </Button>
        </div>
      </aside>

      <div className="min-w-0">
        <header className="sticky top-0 z-30 border-b bg-background/95 backdrop-blur lg:hidden">
          <div className="flex h-14 items-center justify-between px-4">
            <Wordmark />
            <NavLink to="/profile" aria-label="Open profile" className="rounded-full p-1.5 text-muted-foreground hover:bg-accent">
              <CircleUserRound className="size-5" />
            </NavLink>
          </div>
          <nav className="flex gap-1 overflow-x-auto px-3 pb-2 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            {items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "shrink-0 rounded-md px-3 py-1.5 text-sm font-medium",
                    isActive ? "bg-primary/10 text-primary" : "text-muted-foreground",
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </header>

        <main className="mx-auto w-full max-w-7xl px-4 py-7 sm:px-6 sm:py-10 lg:px-10">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
