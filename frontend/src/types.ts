// ── New specialist/validator format ────────────────────────────────────────

export interface SpecialistRisk {
  source: string; // e.g. "labor_economist"
  risk: string;
  mechanism: string;
  severity: 1 | 2 | 3;
  category: string;
  most_exposed: string;
  cities_most_affected: string[];
}

export interface SpecialistResult {
  specialist: string;
  risks: SpecialistRisk[];
}

export interface ValidatorValidation {
  risk_index: number; // 1-based, maps to specialist_risks array
  applies: boolean;
  severity_for_me: 0 | 1 | 2 | 3;
  reason: string;
}

export interface MissedRisk {
  risk: string;
  category: string;
  severity: 1 | 2 | 3;
}

export interface ValidatorResult {
  agent_id: number;
  city: string;
  tenure: 'renter' | 'owner';
  age_bracket: string;
  income_bracket: string;
  immigration_status: string;
  family_size: string;
  employment_type: string;
  population_weight: number;
  validations: ValidatorValidation[];
  missed_risk: MissedRisk | null;
}

export interface RiskReportItem {
  rank: number;
  title: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  reasoning: string;
  affected_groups: string;
  confirmed_by: number;
  out_of: number;
  cities: string[];
  cascade_effect: string | null;
}

export interface RiskReport {
  risks: RiskReportItem[];
  blind_spots: string;
  overall_risk_level: 'HIGH' | 'MEDIUM' | 'LOW';
  key_insight: string;
}

export interface SimulationOutput {
  policy: string;
  total_time_seconds: number;
  specialists_total: number;
  validators_total: number;
  models: {
    specialist: string;
    validator: string;
    coordinator: string;
  };
  round_1_specialists: SpecialistResult[];
  specialist_risks: SpecialistRisk[];
  round_2_validators: ValidatorResult[];
  risk_report: RiskReport;
  confidence?: {
    score: number;
    out_of: number;
    reason: string;
    caveat: string;
  };
  policy_classification?: {
    type: string;
    primary_affected: string;
    market: string;
    geography: string;
    time_horizon: string;
    key_attributes: string[];
  };
  seal_id?: string;
}

// ── Stage2 animation entry ──────────────────────────────────────────────────

export interface AnimationEntry {
  id: number;
  label: string;      // city or specialist title (short)
  sublabel: string;   // tenure/age or specialist category
  concern: string;    // top risk text
  signal: 'positive' | 'negative' | 'mixed';
}

// ── SSE events from server ──────────────────────────────────────────────────

export type SimulationEvent =
  | { type: 'status'; message: string }
  | { type: 'r1_complete'; specialists: SpecialistResult[]; specialist_risks: SpecialistRisk[] }
  | { type: 'r2_complete'; validators: ValidatorResult[] }
  | { type: 'done'; data: SimulationOutput }
  | { type: 'error'; message: string };
