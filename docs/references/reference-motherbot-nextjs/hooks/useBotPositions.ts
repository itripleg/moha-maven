"use client";

import { useMemo } from "react";
import { db } from "@/firebase";
import { collection, query, orderBy, where } from "firebase/firestore";
import { useFirestoreListener } from "./useFirestoreListener";
import type { BotPosition } from "../types";

export function useBotPositions(status: "open" | "closed" | "all" = "all") {
  const q = useMemo(() => {
    // Build query with optional status filter
    if (status !== "all") {
      return query(
        collection(db, "llm-bot-positions"),
        where("status", "==", status),
        orderBy("timestamp", "desc")
      );
    }
    return query(
      collection(db, "llm-bot-positions"),
      orderBy("timestamp", "desc")
    );
  }, [status]);

  const { data: positions, loading, error } = useFirestoreListener<BotPosition[]>(q);

  return { positions: positions || [], loading, error };
}
