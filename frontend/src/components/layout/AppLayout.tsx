import { NavLink, Outlet } from "react-router-dom";

import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/today", label: "Today" },
  { to: "/progress", label: "Progress" },
  { to: "/subscription", label: "Subscription" },
  { to: "/admin", label: "Admin" },
];

export function AppLayout() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b">
        <div className="container flex h-14 items-center justify-between">
          <NavLink to="/dashboard" className="font-semibold tracking-tight">
            CodePath AI
          </NavLink>
          <nav className="flex items-center gap-1">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "rounded-md px-3 py-1.5 text-sm transition-colors hover:bg-accent",
                    isActive ? "bg-accent text-accent-foreground" : "text-muted-foreground",
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="container py-8">
        <Outlet />
      </main>
    </div>
  );
}
