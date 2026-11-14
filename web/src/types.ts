export type Effect = { effect: number | null; note: string };

export type Plan = {
  key: "current" | "cover" | "rotation";
  title: string;
  weeks: string[];
  crops: number[];
  counts: {
    bare: number;
    bare_seen: number;
    bare_likely: number;
    exposed: number;
    exposed_seen: number;
    exposed_likely: number;
    unknown: number;
  };
  score: number;
  grade: string;
  reason: string;
  swap_year?: number | null;
  rationale: string;
  evidence: string;
  benefits: string;
  gaps: string;
  risks: string;
  review: string;
  water: Effect;
  income: Effect;
  cites: string[];
};

export type Soil = {
  name: string;
  kw: number | null;
  om: number | null;
  awc: number | null;
};

export type Field = {
  id: string;
  ha: number;
  years: number[];
  ndvi: (number | null)[][];
  plans: Plan[];
  soil: Soil | null;
};

export type CropInfo = { name: string; color: string; legume: boolean; perennial: boolean };

export type Measure = { normal: number; recent: number };

export type Meta = {
  generated: string;
  box: [number, number, number, number];
  years: number[];
  fields: number;
  hectares: number;
  ndvi_threshold: number;
  heavy: string[];
  heavy_mm: number;
  rain: (number | null)[][];
  climate: {
    normal_years: [number, number];
    recent_years: [number, number];
    measures: Record<"hot_days" | "last_spring_frost" | "first_fall_frost" | "rain_mm", Measure>;
  };
  crops: Record<string, CropInfo>;
  grades: Record<string, number>;
  bare_in_heavy_rain_share: number;
  sources: Record<string, { title: string; url: string }>;
};
