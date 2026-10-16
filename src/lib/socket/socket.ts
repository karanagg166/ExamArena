// src/lib/socket/socket.ts

import { SocketEvents, type SocketEventType, type SocketMessage } from "./event";

type EventHandler<T = unknown> = (data: T) => void;

export class ExamWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 2000;
  private handlers = new Map<string, Set<EventHandler>>();
  private queuedMessages: string[] = [];
  private isExplicitlyClosed = false;
  private heartbeatTimer: NodeJS.Timeout | null = null;

  constructor(endpoint = "/ws") {
    const baseUrl =
      process.env.NEXT_PUBLIC_API_URL ||
      (typeof window !== "undefined" ? window.location.origin : "http://localhost:8000");

    const wsProtocol = baseUrl.startsWith("https") ? "wss" : "ws";
    const cleanHost = baseUrl.replace(/^https?:\/\//, "").replace(/\/$/, "");
    this.url = `${wsProtocol}://${cleanHost}${endpoint}`;
  }

  public connect(authToken?: string): void {
    if (typeof window === "undefined") return;
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.isExplicitlyClosed = false;
    const connectUrl = authToken
      ? `${this.url}?token=${encodeURIComponent(authToken)}`
      : this.url;

    try {
      this.ws = new WebSocket(connectUrl);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.startHeartbeat();
        this.emit(SocketEvents.CONNECT, { url: this.url });

        // Flush queued messages
        while (this.queuedMessages.length > 0) {
          const msg = this.queuedMessages.shift();
          if (msg) this.ws?.send(msg);
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const parsed: SocketMessage = JSON.parse(event.data);
          if (parsed && parsed.event) {
            this.emit(parsed.event, parsed.data);
          }
        } catch {
          // Plain message fallback
          this.emit("raw", event.data);
        }
      };

      this.ws.onclose = () => {
        this.stopHeartbeat();
        this.emit(SocketEvents.DISCONNECT, {});
        if (!this.isExplicitlyClosed) {
          this.scheduleReconnect(authToken);
        }
      };

      this.ws.onerror = (err) => {
        this.emit(SocketEvents.ERROR, err);
      };
    } catch (err) {
      this.emit(SocketEvents.ERROR, err);
    }
  }

  private scheduleReconnect(authToken?: string): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    this.reconnectAttempts += 1;
    const delay = this.reconnectInterval * Math.pow(1.5, this.reconnectAttempts - 1);
    setTimeout(() => {
      if (!this.isExplicitlyClosed) {
        this.connect(authToken);
      }
    }, delay);
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      this.send(SocketEvents.HEARTBEAT, { timestamp: Date.now() });
    }, 30000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  public send<T = unknown>(event: SocketEventType, data: T): void {
    const payload: SocketMessage<T> = {
      event,
      data,
      timestamp: new Date().toISOString(),
    };
    const serialized = JSON.stringify(payload);

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(serialized);
    } else {
      this.queuedMessages.push(serialized);
    }
  }

  public on<T = unknown>(event: string, handler: EventHandler<T>): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)?.add(handler as EventHandler);

    return () => {
      this.off(event, handler as EventHandler);
    };
  }

  public off(event: string, handler: EventHandler): void {
    this.handlers.get(event)?.delete(handler);
  }

  private emit(event: string, data: unknown): void {
    const set = this.handlers.get(event);
    if (set) {
      set.forEach((fn) => {
        try {
          fn(data);
        } catch (e) {
          console.error(`Socket handler error for ${event}:`, e);
        }
      });
    }
  }

  public disconnect(): void {
    this.isExplicitlyClosed = true;
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  public get isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

export const socketClient = new ExamWebSocketClient();
