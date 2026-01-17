"use client";

import { useMemo } from "react";
import { db } from "@/firebase";
import { collection, query, orderBy, limit as firestoreLimit } from "firebase/firestore";
import { useFirestoreListener } from "./useFirestoreListener";
import type { BotAccountState, AccountHistoryPoint } from "../types";

export function useBotAccount() {
  const q = useMemo(() => query(
    collection(db, "llm-bot-account"),
    orderBy("timestamp", "desc"),
    firestoreLimit(1)
  ), []);

  const { data, loading, error } = useFirestoreListener<BotAccountState[]>(q);

  // Extract single account from array
  const account = data && data.length > 0 ? data[0] : null;

  return { account, loading, error };
}

export function useBotAccountHistory(limit: number = 100) {
  const q = useMemo(() => query(
    collection(db, "llm-bot-account"),
    orderBy("timestamp", "desc"),
    firestoreLimit(limit)
  ), [limit]);

  const { data: history, loading, error } = useFirestoreListener<AccountHistoryPoint[]>(q);

  return { history: history || [], loading, error };
}
