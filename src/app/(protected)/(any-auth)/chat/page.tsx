"use client";

import React, { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { StreamChat, Channel as StreamChannel } from "stream-chat";
import {
  Chat,
  Channel,
  ChannelList,
  Window,
  ChannelHeader,
  MessageList,
  MessageInput,
  Thread,
} from "stream-chat-react";
import "stream-chat-react/dist/css/v2/index.css";

import { api } from "@/lib/axios";
import { useAuthStore } from "@/stores";
import { Spinner } from "@/components/ui/loading";
import {
  MessageSquare,
  Users,
  Building2,
  Plus,
  X,
  Search,
  School,
  GraduationCap,
} from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";

export default function ChatPage() {
  const { user } = useAuthStore();
  const { theme } = useTheme();
  const [chatClient, setChatClient] = useState<StreamChat | null>(null);
  const [loading, setLoading] = useState(true);
  const [dmModalOpen, setDmModalOpen] = useState(false);
  const [availableUsers, setAvailableUsers] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [fetchingUsers, setFetchingUsers] = useState(false);
  const [activeChannelId, setActiveChannelId] = useState<string | null>(null);

  // 1. Fetch token and initialize GetStream client
  useEffect(() => {
    if (!user) return;

    let activeClient: StreamChat | null = null;

    const initChat = async () => {
      try {
        setLoading(true);
        // Get JWT from FastAPI backend
        const tokenRes = await api.get("/api/v1/auth/stream-token");
        const { token, apiKey } = tokenRes.data;

        const client = StreamChat.getInstance(apiKey);
        activeClient = client;

        // Connect user
        if (client.userID !== user.id) {
          await client.connectUser(
            {
              id: user.id,
              name: user.name,
              image: `https://getstream.io/random_png/?id=${user.id}&name=${encodeURIComponent(
                user.name,
              )}`,
            },
            token,
          );
        }

        // Fetch user's school and class association from the database to provision channels
        let schoolId = "";
        let schoolName = "";
        let classId = "";
        let className = "";

        try {
          if (user.role === "STUDENT") {
            const studentRes = await api.get("/api/v1/students/me");
            schoolId = studentRes.data.schoolId || "";
            classId = studentRes.data.classId || "";

            if (schoolId) {
              const sRes = await api.get(`/api/v1/schools/${schoolId}`);
              schoolName = sRes.data.name;
            }
            if (classId) {
              const cRes = await api.get(`/api/v1/classes/${classId}`);
              className = cRes.data.name;
            }
          } else if (user.role === "TEACHER") {
            const teacherRes = await api.get("/api/v1/teachers/me");
            schoolId = teacherRes.data.schoolId || "";
            if (schoolId) {
              const sRes = await api.get(`/api/v1/schools/${schoolId}`);
              schoolName = sRes.data.name;
            }
          } else if (user.role === "PRINCIPAL") {
            const principalRes = await api
              .get("/api/v1/principals/me")
              .catch(() => null);
            if (principalRes) {
              schoolId = principalRes.data.schoolId || "";
              if (schoolId) {
                const sRes = await api.get(`/api/v1/schools/${schoolId}`);
                schoolName = sRes.data.name;
              }
            }
          }
        } catch (assocErr) {
          console.error("Failed to load school/class associations:", assocErr);
        }

        // Auto-provision and join channels in GetStream
        if (schoolId) {
          const schoolChannel = client.channel("messaging", `school-${schoolId}`, {
            name: `${schoolName || "School Hub"}`,
            members: [user.id],
            image: "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=100&h=100&fit=crop",
          });
          await schoolChannel.create();
          await schoolChannel.watch();
        }

        if (classId) {
          const classChannel = client.channel("messaging", `class-${classId}`, {
            name: `${className || "Classroom Hub"}`,
            members: [user.id],
            image: "https://images.unsplash.com/photo-1427504494785-3a9ca7044f45?w=100&h=100&fit=crop",
          });
          await classChannel.create();
          await classChannel.watch();
        }

        setChatClient(client);
      } catch (err) {
        console.error("Stream Chat initialization error:", err);
      } finally {
        setLoading(false);
      }
    };

    initChat();

    return () => {
      if (activeClient) {
        activeClient.disconnectUser();
      }
    };
  }, [user]);

  // Load available users for starting Direct Messages
  const loadAvailableUsers = async () => {
    if (!user) return;
    setFetchingUsers(true);
    try {
      const usersList: any[] = [];

      // 1. Fetch Students
      try {
        const studentRes = await api.get("/api/v1/students/");
        if (Array.isArray(studentRes.data)) {
          studentRes.data.forEach((student: any) => {
            const studentUserId = student.userId || student.user?.id;
            const studentName = student.name || student.user?.name;
            if (studentUserId && studentUserId !== user.id) {
              usersList.push({
                id: studentUserId,
                name: studentName || "Student",
                role: "STUDENT",
                email: student.email || student.user?.email,
              });
            }
          });
        }
      } catch (e) {
        console.error("Failed to load students directory:", e);
      }

      // 2. Fetch Teachers
      try {
        const teacherRes = await api.get("/api/v1/teachers/");
        if (Array.isArray(teacherRes.data)) {
          teacherRes.data.forEach((teacher: any) => {
            const teacherUserId = teacher.userId || teacher.user?.id;
            const teacherName = teacher.name || teacher.user?.name;
            if (teacherUserId && teacherUserId !== user.id) {
              usersList.push({
                id: teacherUserId,
                name: teacherName || "Teacher",
                role: "TEACHER",
                email: teacher.email || teacher.user?.email,
              });
            }
          });
        }
      } catch (e) {
        console.error("Failed to load teachers directory:", e);
      }

      // Deduplicate by user ID
      const uniqueUsers = Array.from(
        new Map(usersList.map((item) => [item.id, item])).values(),
      );
      setAvailableUsers(uniqueUsers);
    } catch (err) {
      console.error("Error loading chat directory:", err);
    } finally {
      setFetchingUsers(false);
    }
  };

  useEffect(() => {
    if (dmModalOpen) {
      loadAvailableUsers();
    }
  }, [dmModalOpen]);

  // Handle starting a 1-to-1 Direct Message channel
  const startDirectMessage = async (targetUser: any) => {
    if (!chatClient || !user) return;
    try {
      // Connect / watch the 1-to-1 conversation
      const channel = chatClient.channel("messaging", {
        members: [user.id, targetUser.id],
      });
      await channel.create();
      await channel.watch();

      setDmModalOpen(false);
      // Select the new channel
      setActiveChannelId(channel.id || null);
    } catch (err) {
      console.error("Error initiating Direct Message channel:", err);
    }
  };

  const filteredUsers = availableUsers.filter((u) =>
    u.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.email?.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  if (loading || !chatClient) {
    return (
      <div className="flex min-h-[70vh] flex-col items-center justify-center space-y-4">
        <Spinner className="h-10 w-10 border-4 border-indigo-600 border-t-transparent" />
        <p className="text-sm font-medium text-[var(--text-secondary)]">
          Connecting to Arena Chat Room...
        </p>
      </div>
    );
  }

  // Filter channel list so only channels the user belongs to are shown
  const channelFilters = {
    members: { $in: [user?.id ?? ""] },
  };

  const channelSort = { last_message_at: -1 as const };
  const channelOptions = { watch: true, state: true };

  const isDarkMode = theme === "dark";

  return (
    <div className="page-shell-wide h-[calc(100vh-4rem)] flex flex-col p-4 md:p-6 animate-fade-in">
      {/* Upper Dashboard Header */}
      <div className="flex items-center justify-between mb-4 shrink-0">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)] flex items-center gap-2">
            <MessageSquare className="h-6 w-6 text-indigo-500" />
            Arena Chat Room
          </h1>
          <p className="text-xs text-[var(--text-secondary)]">
            Connect with schools, classmates, and teachers in real-time.
          </p>
        </div>

        <button
          onClick={() => setDmModalOpen(true)}
          className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-500 transition-smooth press-scale"
        >
          <Plus className="h-4 w-4" />
          New Chat / DM
        </button>
      </div>

      {/* Main Chat Framework Wrapper */}
      <div className="flex-1 min-h-0 relative rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-1)] shadow-md overflow-hidden flex flex-col">
        <Chat client={chatClient} theme={isDarkMode ? "str-chat__theme-dark" : "str-chat__theme-light"}>
          <div className="flex flex-1 min-h-0">
            {/* Sidebar list of channels */}
            <aside className="w-80 border-r border-[var(--border-subtle)] bg-[var(--surface-2)] flex flex-col shrink-0">
              <div className="px-4 py-3 border-b border-[var(--border-subtle)] shrink-0 flex items-center justify-between bg-[var(--surface-1)]">
                <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] flex items-center gap-1.5">
                  <Users className="h-3.5 w-3.5" />
                  Your Channels
                </span>
              </div>
              <div className="flex-1 overflow-y-auto">
                <ChannelList
                  filters={channelFilters}
                  sort={channelSort}
                  options={channelOptions}
                  showChannelSearch
                />
              </div>
            </aside>

            {/* Conversation Window */}
            <main className="flex-1 flex flex-col min-w-0 bg-[var(--surface-1)]">
              <Channel>
                <Window>
                  <ChannelHeader />
                  <MessageList />
                  <MessageInput />
                </Window>
                <Thread />
              </Channel>
            </main>
          </div>
        </Chat>
      </div>

      {/* New DM Modal */}
      {dmModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md overflow-hidden rounded-2xl border border-[var(--border-subtle)] bg-[var(--surface-1)] shadow-xl animate-scale-in">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-subtle)]">
              <h3 className="text-base font-bold text-[var(--text-primary)]">
                Start a New Chat
              </h3>
              <button
                onClick={() => setDmModalOpen(false)}
                className="rounded-lg p-1.5 text-[var(--text-secondary)] hover:bg-[var(--surface-2)] transition-smooth"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Search Bar */}
            <div className="p-4 border-b border-[var(--border-subtle)] bg-[var(--surface-2)]">
              <div className="relative">
                <Search className="absolute left-3.5 top-3 h-4 w-4 text-[var(--text-dimmed)]" />
                <input
                  type="text"
                  placeholder="Search by name or email..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-1)] py-2 pl-10 pr-4 text-xs outline-none text-[var(--text-primary)] focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>
            </div>

            {/* User Directory List */}
            <div className="max-h-[300px] overflow-y-auto p-2">
              {fetchingUsers ? (
                <div className="flex flex-col items-center justify-center py-10 space-y-2">
                  <Spinner className="h-6 w-6 border-2 border-indigo-500 border-t-transparent" />
                  <span className="text-xs text-[var(--text-secondary)]">
                    Loading school directory...
                  </span>
                </div>
              ) : filteredUsers.length > 0 ? (
                filteredUsers.map((u) => (
                  <button
                    key={u.id}
                    onClick={() => startDirectMessage(u)}
                    className="w-full flex items-center justify-between rounded-xl p-3 text-left hover:bg-[var(--surface-2)] transition-smooth press-scale"
                  >
                    <div>
                      <h4 className="text-sm font-semibold text-[var(--text-primary)]">
                        {u.name}
                      </h4>
                      <p className="text-xs text-[var(--text-muted)] mt-0.5">
                        {u.email}
                      </p>
                    </div>
                    <Badge
                      variant={u.role === "TEACHER" ? "success" : "default"}
                      className="text-[10px]"
                    >
                      {u.role}
                    </Badge>
                  </button>
                ))
              ) : (
                <div className="py-10 text-center">
                  <p className="text-xs text-[var(--text-muted)]">
                    No matching classmates or teachers found.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
