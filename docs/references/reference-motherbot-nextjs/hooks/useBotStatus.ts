"use client";

import { useState, useCallback, useMemo } from "react";
import { db } from "@/firebase";
import { collection, query, orderBy, limit as firestoreLimit } from "firebase/firestore";
import { useFirestoreListener } from "./useFirestoreListener";
import type { BotStatus, BotControlResponse } from "../types";

export function useBotStatus() {
  const q = useMemo(() => query(
    collection(db, "llm-bot-status"),
    orderBy("timestamp", "desc"),
    firestoreLimit(1)
  ), []);

  const { data, loading, error } = useFirestoreListener<BotStatus[]>(q);

  // Extract single status from array
  const status = data && data.length > 0 ? data[0] : null;

  return { status, loading, error };
}

export function useBotControls() {
  const [controlling, setControlling] = useState(false);

  const startBot = useCallback(async (): Promise<BotControlResponse> => {
    setControlling(true);
    try {
      const response = await fetch("/api/llm-bot/controls/start", {
        method: "POST",
      });
      const data = await response.json();
      return data;
    } catch (err) {
      return {
        success: false,
        message: err instanceof Error ? err.message : "Failed to start bot",
      };
    } finally {
      setControlling(false);
    }
  }, []);

  const stopBot = useCallback(async (): Promise<BotControlResponse> => {
    setControlling(true);
    try {
      const response = await fetch("/api/llm-bot/controls/stop", {
        method: "POST",
      });
      const data = await response.json();
      return data;
    } catch (err) {
      return {
        success: false,
        message: err instanceof Error ? err.message : "Failed to stop bot",
      };
    } finally {
      setControlling(false);
    }
  }, []);

  const emergencyStop = useCallback(async (): Promise<BotControlResponse> => {
    setControlling(true);
    try {
      const response = await fetch("/api/llm-bot/controls/emergency", {
        method: "POST",
      });
      const data = await response.json();
      return data;
    } catch (err) {
      return {
        success: false,
        message: err instanceof Error ? err.message : "Emergency stop failed",
      };
    } finally {
      setControlling(false);
    }
  }, []);

  return { startBot, stopBot, emergencyStop, controlling };
}
