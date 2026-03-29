import { StudentProfileResponse } from "@/types/student";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Mail, Phone, MapPin, Calendar, User, Hash, Users } from "lucide-react";

export default function StudentProfileCard({
  student,
}: {
  student: StudentProfileResponse;
}) {
  const { user } = student;

  const formatDate = (ds: string) => {
    try {
      if (!ds) return "N/A";
      const formatOptions: Intl.DateTimeFormatOptions = {
        month: "short",
        day: "2-digit",
        year: "numeric",
      };
      return new Intl.DateTimeFormat("en-US", formatOptions).format(
        new Date(ds),
      );
    } catch {
      return "Invalid date";
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <Card className="overflow-hidden border-none shadow-xl bg-gradient-to-br from-emerald-50 to-white dark:from-slate-900 dark:to-slate-950">
        <div className="h-32 bg-emerald-600/10 dark:bg-emerald-600/20 w-full" />
        <CardContent className="relative px-8 pb-8 pt-0">
          <div className="-mt-16 mb-4 relative z-10 flex flex-col md:flex-row items-center md:items-end gap-6">
            <div className="w-32 h-32 rounded-2xl bg-white dark:bg-slate-800 p-2 shadow-lg flex-shrink-0 border border-emerald-100 dark:border-emerald-900/50">
              <div className="w-full h-full bg-emerald-50 dark:bg-emerald-900/20 rounded-xl flex items-center justify-center text-emerald-500">
                <User size={48} className="opacity-50" />
              </div>
            </div>
            <div className="flex-1 text-center md:text-left mb-2">
              <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                {user.name}
              </h1>
              <p className="text-emerald-600 dark:text-emerald-400 font-medium flex items-center justify-center md:justify-start gap-2 mt-1">
                <Hash size={16} />
                Roll No: {student.rollNo} • Admitted{" "}
                {formatDate(student.dateOfAdmission)}
              </p>
            </div>
            <div className="mb-2 hidden md:block">
              <Badge className="px-4 py-2 text-sm bg-emerald-100 text-emerald-800 hover:bg-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 border-none shadow-sm">
                Student
              </Badge>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mt-8 border-t border-slate-100 dark:border-slate-800/50 pt-8">
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                Personal Information
              </h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3 text-slate-700 dark:text-slate-300">
                  <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500">
                    <Calendar size={16} />
                  </div>
                  <span>Date of Birth: {formatDate(student.dob)}</span>
                </div>
                <div className="flex items-center gap-3 text-slate-700 dark:text-slate-300">
                  <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500">
                    <Mail size={16} />
                  </div>
                  <span>{user.email}</span>
                </div>
                <div className="flex items-center gap-3 text-slate-700 dark:text-slate-300">
                  <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500">
                    <Phone size={16} />
                  </div>
                  <span>{user.phoneNo}</span>
                </div>
                <div className="flex items-start gap-3 text-slate-700 dark:text-slate-300 mt-2">
                  <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500 flex-shrink-0 mt-1">
                    <MapPin size={16} />
                  </div>
                  <span className="mt-1 leading-relaxed">
                    {[user.city, user.state, user.country, user.pincode]
                      .filter(Boolean)
                      .join(", ") || "No address provided"}
                  </span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-sm font-semibold flex items-center gap-2 text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                <Users size={16} />
                Guardian Details
              </h3>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-500">Parent Name</span>
                  <span className="font-medium text-slate-800 dark:text-slate-200">
                    {student.parentName}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-500">Parent Email</span>
                  <a
                    href={`mailto:${student.parentEmail}`}
                    className="font-medium text-emerald-600 hover:underline"
                  >
                    {student.parentEmail}
                  </a>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
