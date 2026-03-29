import { TeacherProfileResponse } from "@/types/teacher";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Mail,
  Phone,
  MapPin,
  GraduationCap,
  BookOpen,
  Briefcase,
  User,
} from "lucide-react";

export default function TeacherProfileCard({
  teacher,
}: {
  teacher: TeacherProfileResponse;
}) {
  const { user } = teacher;

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <Card className="overflow-hidden border-none shadow-xl bg-gradient-to-br from-indigo-50 to-white dark:from-slate-900 dark:to-slate-950">
        <div className="h-32 bg-indigo-600/10 dark:bg-indigo-600/20 w-full" />
        <CardContent className="relative px-8 pb-8 pt-0">
          <div className="-mt-16 mb-4 relative z-10 flex flex-col md:flex-row items-center md:items-end gap-6">
            <div className="w-32 h-32 rounded-2xl bg-white dark:bg-slate-800 p-2 shadow-lg flex-shrink-0 border border-indigo-100 dark:border-indigo-900/50">
              <div className="w-full h-full bg-indigo-50 dark:bg-indigo-900/20 rounded-xl flex items-center justify-center text-indigo-500">
                <User size={48} className="opacity-50" />
              </div>
            </div>
            <div className="flex-1 text-center md:text-left mb-2">
              <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                {user.name}
              </h1>
              <p className="text-indigo-600 dark:text-indigo-400 font-medium flex items-center justify-center md:justify-start gap-2 mt-1">
                <Briefcase size={16} />
                {teacher.department} Department • {teacher.experience} Years
                Experience
              </p>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mt-8 border-t border-slate-100 dark:border-slate-800/50 pt-8">
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                Contact Information
              </h3>
              <div className="space-y-3">
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
                <div className="flex items-start gap-3 text-slate-700 dark:text-slate-300">
                  <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500 mt-1">
                    <MapPin size={16} />
                  </div>
                  <span className="mt-1">
                    {[user.city, user.state, user.country, user.pincode]
                      .filter(Boolean)
                      .join(", ") || "No address provided"}
                  </span>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-sm font-semibold flex items-center gap-2 text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                  <GraduationCap size={16} />
                  Qualifications
                </h3>
                <div className="flex flex-wrap gap-2">
                  {teacher.qualifications?.length > 0 ? (
                    teacher.qualifications.map((qual, i) => (
                      <Badge
                        key={i}
                        variant="neutral"
                        className="px-3 py-1 bg-blue-50 text-blue-700 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-300 border-none"
                      >
                        {qual}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-slate-400 text-sm italic">
                      Not specified
                    </span>
                  )}
                </div>
              </div>

              <div className="space-y-4 border-t border-slate-100 dark:border-slate-800/50 pt-6">
                <h3 className="text-sm font-semibold flex items-center gap-2 text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                  <BookOpen size={16} />
                  Subjects Taught
                </h3>
                <div className="flex flex-wrap gap-2">
                  {teacher.subjects?.length > 0 ? (
                    teacher.subjects.map((sub, i) => (
                      <Badge
                        key={i}
                        className="px-3 py-1 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 dark:bg-indigo-900/30 dark:text-indigo-300 border-none"
                      >
                        {sub}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-slate-400 text-sm italic">
                      Not specified
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
