"use client";

import { useMemo } from "react";
import { db } from "@/firebase";
import { collection, query, orderBy, limit as firestoreLimit, where } from "firebase/firestore";
import { useFirestoreListener } from "./useFirestoreListener";
import type { BotDecision } from "../types";

export function useBotDecisions(limit: number = 20, coin?: string) {
  const q = useMemo(() => {
    // Build query with optional coin filter
    if (coin) {
      return query(
        collection(db, "llm-bot-decisions"),
        where("coin", "==", coin),
        orderBy("timestamp", "desc"),
        firestoreLimit(limit)
      );
    }
    return query(
      collection(db, "llm-bot-decisions"),
      orderBy("timestamp", "desc"),
      firestoreLimit(limit)
    );
  }, [limit, coin]);

  const { data: decisions, loading, error } = useFirestoreListener<BotDecision[]>(q);

  return { decisions: decisions || [], loading, error };
}
