"use client";

import { useState, useEffect } from "react";
import { onSnapshot, Query, FirestoreError } from "firebase/firestore";

interface UseFirestoreListenerOptions<T> {
  enabled?: boolean;
  transform?: (data: any) => T;
}

interface UseFirestoreListenerResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/**
 * Generic Firestore real-time listener hook
 * Eliminates boilerplate code across all bot hooks
 */
export function useFirestoreListener<T>(
  query: Query | null,
  options: UseFirestoreListenerOptions<T> = {}
): UseFirestoreListenerResult<T> {
  const { enabled = true, transform } = options;
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled || !query) {
      setLoading(false);
      return;
    }

    try {
      const unsubscribe = onSnapshot(
        query,
        (snapshot) => {
          try {
            const rawData = snapshot.docs.map(doc => ({
              id: doc.id,
              ...doc.data()
            }));

            // Apply transform if provided, otherwise use raw data
            const transformedData = transform
              ? transform(rawData)
              : (rawData as unknown as T);

            setData(transformedData);
            setError(null);
            setLoading(false);
          } catch (err) {
            const errorMsg = err instanceof Error ? err.message : "Data transformation failed";
            setError(errorMsg);
            console.error("Error processing snapshot data:", err);
            setLoading(false);
          }
        },
        (err: FirestoreError) => {
          setError(err.message);
          console.error("Error in Firestore listener:", err);
          setLoading(false);
        }
      );

      return () => unsubscribe();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to setup listener";
      setError(errorMsg);
      console.error("Error setting up Firestore listener:", err);
      setLoading(false);
    }
  }, [query, enabled, transform]);

  return { data, loading, error };
}
