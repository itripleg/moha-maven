// app/motherbot/components/TradingViewWidget.tsx
"use client";

import { Card, CardContent } from "@/components/ui/card";
import { useEffect, useRef } from "react";

interface TradingViewWidgetProps {
  selectedPair: string;
}

export function TradingViewWidget({ selectedPair }: TradingViewWidgetProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Get symbol for TradingView
    const coin = selectedPair === "ALL" ? "BTC" : selectedPair.split('/')[0];
    const symbol = `BINANCE:${coin}USDT`;

    // Clear previous widget
    containerRef.current.innerHTML = "";

    // Create TradingView widget script
    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/tv.js";
    script.async = true;
    script.onload = () => {
      if (typeof (window as any).TradingView !== "undefined") {
        new (window as any).TradingView.widget({
          autosize: true,
          symbol: symbol,
          interval: "60", // 1 hour
          timezone: "Etc/UTC",
          theme: "dark",
          style: "1",
          locale: "en",
          toolbar_bg: "#f1f3f6",
          enable_publishing: false,
          hide_top_toolbar: false,
          hide_legend: false,
          save_image: false,
          container_id: "tradingview_widget",
        });
      }
    };

    const widgetDiv = document.createElement("div");
    widgetDiv.id = "tradingview_widget";
    widgetDiv.style.height = "100%";
    containerRef.current.appendChild(widgetDiv);
    document.body.appendChild(script);

    return () => {
      // Cleanup
      if (script.parentNode) {
        script.parentNode.removeChild(script);
      }
    };
  }, [selectedPair]);

  return (
    <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
      <CardContent className="pt-6">
        <div ref={containerRef} className="w-full h-[370px] rounded-lg overflow-hidden" />
      </CardContent>
    </Card>
  );
}
