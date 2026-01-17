// app/motherbot/components/chart/types.ts
export type TimeFrame = "1h" | "6h" | "1d" | "7d" | "30d" | "all";

export interface ChartDataPoint {
  timestamp: string;
  balance: number;
  buyAndHold?: number;
}

export interface ProcessedChartData {
  points: ChartDataPoint[];
  timeFrame: TimeFrame;
  tickInterval: number;
  dateFormat: string;
}
