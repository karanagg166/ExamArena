"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { StreamChat, type Channel } from "stream-chat";
import { api } from "@/lib/axios";
import { useAuthStore } from "@/stores";

interface UseChatReturn {
  client: StreamChat | null;
  loading: boolean;
  error: string | null;
  unreadCount: number;
  openDirectChannel: (targetUserId: string) => Promise<Channel | null>;
}

export function useChat(): UseChatReturn {
  const { user } = useAuthStore();
  const [client, setClient] = useState<StreamChat | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const activeClientRef = useRef<StreamChat | null>(null);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    let isMounted = true;

    const setupChat = async () => {
      try {
        setLoading(true);
        setError(null);

        const tokenRes = await api.get<{ token: string; apiKey: string }>("/api/v1/auth/stream-token");
        const { token, apiKey } = tokenRes.data;

        if (!token || !apiKey) {
          throw new Error("Chat authentication tokens are unavailable.");
        }

        const chatClient = StreamChat.getInstance(apiKey);
        activeClientRef.current = chatClient;

        await chatClient.connectUser(
          {
            id: user.id,
            name: user.name,
            role: user.role.toLowerCase(),
          },
          token
        );

        if (isMounted) {
          setClient(chatClient);
          const unread = (chatClient.user as unknown as Record<string, unknown>)?.total_unread_count;
          setUnreadCount(typeof unread === "number" ? unread : 0);

          chatClient.on("notification.message_new", () => {
            if (isMounted) {
              const count = (chatClient.user as unknown as Record<string, unknown>)?.total_unread_count;
              setUnreadCount(typeof count === "number" ? count : 0);
            }
          });
        }
      } catch (err: unknown) {
        if (isMounted) {
          console.error("Failed to connect to chat service:", err);
          setError(
            (err as Error)?.message || "Failed to establish chat connection."
          );
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    setupChat();

    return () => {
      isMounted = false;
      if (activeClientRef.current) {
        activeClientRef.current.disconnectUser().catch(() => {});
        activeClientRef.current = null;
      }
    };
  }, [user]);

  const openDirectChannel = useCallback(
    async (targetUserId: string): Promise<Channel | null> => {
      if (!client || !user) return null;
      try {
        const channel = client.channel("messaging", {
          members: [user.id, targetUserId],
        });
        await channel.watch();
        return channel;
      } catch (err) {
        console.error("Failed to open direct message channel:", err);
        return null;
      }
    },
    [client, user]
  );

  return {
    client,
    loading,
    error,
    unreadCount,
    openDirectChannel,
  };
}

export default useChat;
