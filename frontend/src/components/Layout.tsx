import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  ClipboardCheck,
  FileText,
  Info,
  LayoutDashboard,
  LogOut,
  ScanLine,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/grade-paper", label: "Grade paper", icon: ScanLine },
  { to: "/questions", label: "Questions", icon: FileText },
  { to: "/score-preview", label: "Score preview", icon: ClipboardCheck },
  { to: "/about", label: "About", icon: Info },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="relative min-h-screen md:flex">
      <aside className="hidden w-60 shrink-0 border-r border-border bg-card/70 md:fixed md:flex md:h-screen md:flex-col md:px-5 md:py-6 animate-slide-in">
        <div className="mb-8 flex items-center gap-3">
          <img
            src="/kiu_logo.png"
            alt="Karakoram International University"
            className="h-11 w-11 shrink-0 object-contain"
          />
          <div className="min-w-0">
            <p className="font-display text-xl font-semibold leading-tight text-foreground">
              AutoScoring
            </p>
            <p className="mt-0.5 text-[11px] leading-snug text-muted-foreground">KIU · Exam grading</p>
          </div>
        </div>

        <nav className="flex flex-1 flex-col gap-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground",
                  isActive && "bg-secondary text-foreground"
                )
              }
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <Separator className="my-4" />
        <div className="space-y-3">
          <div>
            <p className="text-sm font-medium">{user?.name}</p>
            <p className="truncate text-xs text-muted-foreground">{user?.email}</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-2 px-2"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </Button>
        </div>
      </aside>

      <main className="min-h-screen flex-1 px-4 py-6 md:ml-60 md:px-8 md:py-8">
        <div className="mb-6 flex items-center gap-2.5 md:hidden">
          <img src="/kiu_logo.png" alt="" className="h-8 w-8 object-contain" aria-hidden />
          <span className="font-display text-lg font-semibold">AutoScoring</span>
        </div>
        <div className="mx-auto max-w-5xl animate-fade-up">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
