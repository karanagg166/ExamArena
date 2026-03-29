"use client";

import Link from "next/link";
import { useAuthStore } from "@/stores/useAuthStore";
import { Users, Library, UserCircle, ArrowRight } from "lucide-react";

export default function StudentDashboard() {
  const { user } = useAuthStore();

  const links = [
    {
      title: "My Class",
      description:
        "Check out your classmates, class details, and assigned teachers.",
      href: "/student/class",
      icon: Users,
      color: "text-green-500",
      bgHover: "hover:bg-green-500/10",
      borderHover: "hover:border-green-500/30",
    },
    {
      title: "School Facts",
      description: "Learn more about your school's administration and details.",
      href: "/student/school",
      icon: Library,
      color: "text-fuchsia-500",
      bgHover: "hover:bg-fuchsia-500/10",
      borderHover: "hover:border-fuchsia-500/30",
    },
    {
      title: "My Details",
      description:
        "Keep your personal information and student profile up to date.",
      href: "/student/profile",
      icon: UserCircle,
      color: "text-amber-500",
      bgHover: "hover:bg-amber-500/10",
      borderHover: "hover:border-amber-500/30",
    },
  ];

  return (
    <div className="page-shell">
      <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
        {/* Header Section */}
        <div className="bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 rounded-3xl p-8 md:p-12 relative overflow-hidden shadow-2xl">
          <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none">
            <Users size={200} />
          </div>
          <div className="relative z-10">
            <h1 className="text-4xl md:text-5xl font-extrabold text-white tracking-tight mb-4">
              Welcome back, {user?.name?.split(" ")[0] || "Student"}!
            </h1>
            <p className="text-lg text-slate-400 max-w-2xl">
              Your student hub is ready. Dive into your class details, view
              school information, or manage your profile.
            </p>
          </div>
        </div>

        {/* Quick Links Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {links.map((link) => {
            const Icon = link.icon;
            return (
              <Link
                key={link.title}
                href={link.href}
                className={`group block p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm transition-all duration-300 ${link.bgHover} ${link.borderHover} hover:-translate-y-1 hover:shadow-lg`}
              >
                <div className="flex items-center justify-between mb-4">
                  <div
                    className={`p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 ${link.color}`}
                  >
                    <Icon size={24} />
                  </div>
                  <ArrowRight className="w-5 h-5 text-slate-300 dark:text-slate-600 group-hover:text-slate-500 dark:group-hover:text-slate-300 transition-colors" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-2">
                  {link.title}
                </h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  {link.description}
                </p>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
