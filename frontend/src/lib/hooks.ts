import { useQuery } from "@tanstack/react-query";
import { api } from "./api";

export interface SummaryStats {
  total_violations: number;
  active_violations: number;
  congestion_score: number;
  officers_active: number;
  avg_response_time_min: number;
  active_cameras: number;
  resolution_rate: number;
}

export interface TrendPoint {
  date: string;
  count: number;
}

export interface TrendsResponse {
  trends: TrendPoint[];
  days: number;
  zone_id: string | null;
  vehicle_type: string | null;
}

export interface PriorityZone {
  rank: number;
  zone_id: string;
  zone_name: string;
  police_station: string;
  average_impact: number;
  speed_drop_percent: number;
  total_violations: number;
  recommendation: string;
}

export interface Alert {
  zone_id: string;
  zone_name: string;
  severity: string;
  average_impact: number;
  total_violations: number;
  generated_at: string;
}

export interface AlertsResponse {
  alerts: Alert[];
  count: number;
}

export interface ZoneImpact {
  zone_id: string;
  zone_name: string;
  hours: number;
  violation_count: number;
  impact_scores: Array<{
    timestamp: string;
    impact_score: number;
    speed_drop_percent: number;
    violation_count: number;
  }>;
  average_impact: number;
}

export interface HeatmapResponse {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    geometry: { type: "Point"; coordinates: [number, number] };
    properties: { count: number };
  }>;
}

export interface Camera {
  id: string;
  name: string;
  location: string;
  zone_id: string;
  status: string;
  rtsp_url: string | null;
}

export function useSummary() {
  return useQuery<SummaryStats>({
    queryKey: ["summary"],
    queryFn: () => api.get("/api/v1/analytics/summary"),
    refetchInterval: 30000,
  });
}

export function useTrends(days = 7, zoneId?: string, vehicleType?: string) {
  const params = new URLSearchParams({ days: String(days) });
  if (zoneId) params.set("zone_id", zoneId);
  if (vehicleType) params.set("vehicle_type", vehicleType);
  return useQuery<TrendsResponse>({
    queryKey: ["trends", days, zoneId, vehicleType],
    queryFn: () => api.get(`/api/v1/analytics/trends?${params}`),
  });
}

export function useHeatmap(hours = 24) {
  return useQuery<HeatmapResponse>({
    queryKey: ["heatmap", hours],
    queryFn: () => api.get(`/api/v1/heatmap?hours=${hours}`),
    refetchInterval: 60000,
  });
}

export function usePriorityQueue(topN = 10, hours = 24) {
  return useQuery<PriorityZone[]>({
    queryKey: ["priority-queue", topN, hours],
    queryFn: () => api.get(`/api/v1/priority-queue?top_n=${topN}&hours=${hours}`),
    refetchInterval: 30000,
  });
}

export function useAlerts() {
  return useQuery<AlertsResponse>({
    queryKey: ["alerts"],
    queryFn: () => api.get("/api/v1/alerts"),
    refetchInterval: 15000,
  });
}

export function useZoneImpact(zoneId: string, hours = 24) {
  return useQuery<ZoneImpact>({
    queryKey: ["zone-impact", zoneId, hours],
    queryFn: () => api.get(`/api/v1/zones/${zoneId}/impact?hours=${hours}`),
    enabled: !!zoneId,
  });
}

export function useDevices() {
  return useQuery<{ streams: Camera[] }>({
    queryKey: ["devices"],
    queryFn: () => api.get("/api/v1/detect/streams"),
  });
}

export interface DispatchOfficer {
  id: string;
  name: string;
  status: string;
  zone: string;
  statLabel: string;
  statVal: string;
  color: string;
}

export interface DispatchAssignment {
  officer: string;
  zone: string;
  violation: string;
  priority: string;
  eta: string;
  status: string;
  color: string;
}

export interface DispatchTimelineEntry {
  time: string;
  text: string;
  icon: string;
}

export interface DispatchOverview {
  officers: DispatchOfficer[];
  assignments: DispatchAssignment[];
  timeline: DispatchTimelineEntry[];
}

export function useDispatchOverview() {
  return useQuery<DispatchOverview>({
    queryKey: ["dispatch-overview"],
    queryFn: () => api.get("/api/v1/dispatch/overview"),
    refetchInterval: 15000,
  });
}

export interface CongestionHeatEntry {
  time: string;
  morning: number;
  afternoon: number;
  evening: number;
}

export function useCongestionHeat(hours = 24) {
  return useQuery<CongestionHeatEntry[]>({
    queryKey: ["congestion-heat", hours],
    queryFn: () => api.get(`/api/v1/analytics/congestion-heat?hours=${hours}`),
    refetchInterval: 60000,
  });
}

export interface ViolationTypeEntry {
  name: string;
  value: number;
  color: string;
}

export function useViolationTypes() {
  return useQuery<ViolationTypeEntry[]>({
    queryKey: ["violation-types"],
    queryFn: () => api.get("/api/v1/analytics/violation-types"),
    refetchInterval: 60000,
  });
}

export interface RadarZoneFactors {
  zone_id: string;
  zone_name: string;
  factors: Record<string, number>;
}

export interface RadarResponse {
  factors: string[];
  zones: RadarZoneFactors[];
}

export function useRadarData(zoneId?: string) {
  const params = zoneId ? `?zone_id=${zoneId}` : "";
  return useQuery<RadarResponse>({
    queryKey: ["radar", zoneId],
    queryFn: () => api.get(`/api/v1/analytics/radar${params}`),
    refetchInterval: 60000,
  });
}

export interface FactorWeightsResponse {
  weights: Record<string, number>;
}

export function useFactorWeights() {
  return useQuery<FactorWeightsResponse>({
    queryKey: ["factor-weights"],
    queryFn: () => api.get("/api/v1/analytics/factor-weights"),
    refetchInterval: 60000,
  });
}

export function useAnalyticsInsights() {
  return useQuery<string[]>({
    queryKey: ["analytics-insights"],
    queryFn: () => api.get("/api/v1/analytics/insights"),
    refetchInterval: 60000,
  });
}

export interface PredictedHotspot {
  name: string;
  confidence: number;
  state?: string;
  hotspot_probability?: number;
}

export function usePredictedHotspots() {
  return useQuery<PredictedHotspot[]>({
    queryKey: ["predicted-hotspots"],
    queryFn: () => api.get("/api/v1/analytics/predicted-hotspots"),
    refetchInterval: 60000,
  });
}
