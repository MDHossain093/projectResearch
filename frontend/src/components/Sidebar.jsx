"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Target,
  ChartColumn,
  Users,
} from "lucide-react";

const menus = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Recommendation",
    href: "/recommendation",
    icon: Target,
  },
  {
    name: "Weakness",
    href: "/weakness",
    icon: ChartColumn,
  },
  {
    name: "Team Builder",
    href: "/team",
    icon: Users,
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900 min-h-screen">
      <div className="p-6">
        <h2 className="text-2xl font-bold text-blue-500">
          CF Recommender
        </h2>
      </div>

      <nav className="px-3 space-y-2">
        {menus.map((item) => {
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-4 py-3 transition ${pathname === item.href
                ? "bg-blue-600 text-white"
                : "text-slate-300 hover:bg-slate-800"
                }`}
            >
              <Icon size={20} />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}