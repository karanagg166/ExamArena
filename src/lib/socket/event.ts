// src/lib/socket/event.ts

export const SocketEvents = {
  // Connection / Lifecycle
  CONNECT: "connect",
  DISCONNECT: "disconnect",
  ERROR: "error",
  HEARTBEAT: "heartbeat",

  // Exam Room Management
  EXAM_JOIN: "exam:join",
  EXAM_LEAVE: "exam:leave",
  EXAM_START: "exam:start",
  EXAM_SUBMIT: "exam:submit",
  EXAM_FORCE_SUBMIT: "exam:force_submit",
  EXAM_TIME_SYNC: "exam:time_sync",

  // Proctoring Violations
  PROCTORING_WARNING: "proctoring:warning",
  PROCTORING_LOG: "proctoring:log",

  // Presence & Chat
  USER_JOINED: "presence:user_joined",
  USER_LEFT: "presence:user_left",
  PRESENCE_SYNC: "presence:sync",
  CHAT_MESSAGE: "chat:message",
} as const;

export type SocketEventType = (typeof SocketEvents)[keyof typeof SocketEvents];

export interface SocketMessage<T = unknown> {
  event: SocketEventType;
  data: T;
  timestamp: string;
}
