// app/motherbot/components/layout/MotherBotPageLayout.tsx
"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MotherBotHeader } from "./MotherBotHeader";
import { MotherBotMainArea } from "./MotherBotMainArea";
import { MotherBotSidebar } from "./MotherBotSidebar";
import type { BotStrategyMode } from "../../types";

export function MotherBotPageLayout() {
  const [strategyMode, setStrategyMode] = useState<BotStrategyMode>("independent");
  const [selectedPair, setSelectedPair] = useState<string>("ALL");

  return (
    <div className="min-h-screen">
      <div className="container mx-auto pt-20 px-4 pb-8 max-w-[1800px]">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-4"
        >
          <MotherBotHeader
            strategyMode={strategyMode}
            onStrategyModeChange={setStrategyMode}
          />
        </motion.div>

        {/* Main Grid Layout */}
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-4 mt-4">
          {/* Left Column - Main Trading Area */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="xl:col-span-3"
          >
            <MotherBotMainArea
              strategyMode={strategyMode}
              selectedPair={selectedPair}
              onSelectPair={setSelectedPair}
            />
          </motion.div>

          {/* Right Sidebar - Controls & Metrics */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="xl:col-span-1"
          >
            <MotherBotSidebar
              strategyMode={strategyMode}
              onStrategyModeChange={setStrategyMode}
              selectedPair={selectedPair}
            />
          </motion.div>
        </div>
      </div>
    </div>
  );
}
