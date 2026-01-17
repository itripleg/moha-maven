"use client";

import { useEffect, useState } from "react";
import { MotherBotPageLayout } from "./components/layout/MotherBotPageLayout";

export default function LLMBotDashboard() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return <MotherBotPageLayout />;
}
// Force rebuild Mon, Nov 17, 2025  5:16:04 PM
