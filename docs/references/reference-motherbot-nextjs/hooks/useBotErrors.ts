"use client";

import { useMemo } from "react";
import { db } from "@/firebase";
import { collection, query, orderBy, where, limit as firestoreLimit } from "firebase/firestore";
import { useFirestoreListener } from "./useFirestoreListener";
import type { BotDecision } from "../types";

export interface ExecutionError {
  decision: BotDecision;
  error: string;
  timestamp: string;
}

export function useBotErrors() {
  const q = useMemo(() => query(
    collection(db, "llm-bot-decisions"),
    where("execution_status", "==", "failed"),
    orderBy("timestamp", "desc"),
    firestoreLimit(50)
  ), []);

  const { data, loading, error: fetchError } = useFirestoreListener<ExecutionError[]>(q, {
    transform: (rawData: BotDecision[]) => {
      return rawData.map(decision => ({
        decision,
        error: decision.execution_error || "Unknown error",
        timestamp: decision.execution_timestamp || decision.timestamp
      }));
    }
  });

  return { errors: data || [], loading, error: fetchError };
}
