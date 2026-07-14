import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";
import { useSessionStore } from "@/store/session";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/today", label: "Today" },
  { to: "/review", label: "Review" },
  { to: "/practice", label: "Practice" },
  { to: "/progress", label: "Progress" },
  { to: "/subscription", label: "Subscription" },
  { to: "/admin", label: "Admin" },
];

export function AppLayout() {
  const navigate = useNavigate();
  const { signOut } = useAuth();
  const user = useSessionStore((s) => s.user);

  async function handleSignOut() {
    await signOut();
    navigate("/login");
  }

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
            <NavLink
              to="/profile"
              className="ml-2 max-w-[12rem] truncate text-sm text-muted-foreground hover:text-foreground"
              title="Profile"
            >
              {user?.displayName || user?.email || "Profile"}
            </NavLink>
            <Button variant="ghost" size="sm" onClick={handleSignOut}>
              Sign out
            </Button>
          </nav>
        </div>
      </header>
      <main className="container py-8">
        <Outlet />
      </main>
    </div>
  );
}
