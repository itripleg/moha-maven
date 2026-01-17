"use client";

import { useMemo } from "react";
import { db } from "@/firebase";
import { collection, query, orderBy, limit } from "firebase/firestore";
import { useFirestoreListener } from "./useFirestoreListener";

export interface DebugInfo {
  latest_prompt?: {
    system_prompt: string;
    user_prompt: string;
    response: string;
    timestamp: string;
  } | null;
}

export function useBotDebug() {
  const q = useMemo(() => query(
    collection(db, "llm-bot-decisions"),
    orderBy("timestamp", "desc"),
    limit(1)
  ), []);

  const { data, loading } = useFirestoreListener<DebugInfo>(q, {
    transform: (rawData: any[]) => {
      if (rawData.length > 0) {
        const latest = rawData[0];
        return {
          latest_prompt: {
            system_prompt: latest.system_prompt || "Not available",
            user_prompt: latest.user_prompt || "Not available",
            response: latest.raw_response || latest.justification,
            timestamp: latest.timestamp
          }
        };
      }
      return { latest_prompt: null };
    }
  });

  return { debugInfo: data || { latest_prompt: null }, loading };
}
