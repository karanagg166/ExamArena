"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { socketClient } from "@/lib/socket/socket";
import { SocketEvents, type SocketEventType } from "@/lib/socket/event";

interface UseSocketOptions {
  examId?: string;
  autoConnect?: boolean;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export function useSocket({
  examId,
  autoConnect = true,
  onConnect,
  onDisconnect,
}: UseSocketOptions = {}) {
  const [connected, setConnected] = useState<boolean>(socketClient.isConnected);
  const onConnectRef = useRef(onConnect);
  const onDisconnectRef = useRef(onDisconnect);

  useEffect(() => {
    onConnectRef.current = onConnect;
    onDisconnectRef.current = onDisconnect;
  }, [onConnect, onDisconnect]);

  useEffect(() => {
    if (!autoConnect) return;

    const unsubConnect = socketClient.on(SocketEvents.CONNECT, () => {
      setConnected(true);
      if (examId) {
        socketClient.send(SocketEvents.EXAM_JOIN, { examId });
      }
      onConnectRef.current?.();
    });

    const unsubDisconnect = socketClient.on(SocketEvents.DISCONNECT, () => {
      setConnected(false);
      onDisconnectRef.current?.();
    });

    socketClient.connect();

    return () => {
      if (examId) {
        socketClient.send(SocketEvents.EXAM_LEAVE, { examId });
      }
      unsubConnect();
      unsubDisconnect();
    };
  }, [autoConnect, examId]);

  const emit = useCallback(<T = unknown>(event: SocketEventType, data: T) => {
    socketClient.send(event, data);
  }, []);

  const subscribe = useCallback(<T = unknown>(event: string, handler: (data: T) => void) => {
    return socketClient.on<T>(event, handler);
  }, []);

  return {
    isConnected: connected,
    emit,
    subscribe,
    connect: () => socketClient.connect(),
    disconnect: () => socketClient.disconnect(),
  };
}

export default useSocket;
