import type {
  SimulationOutput,
  SpecialistRisk,
  ValidatorResult,
} from '../types';

// ── Specialist risks (up to 10, as selected by build_validation_context) ────

const SPECIALIST_RISKS: SpecialistRisk[] = [
  {
    source: 'labor_economist',
    risk: 'Construction labour shortages will stall timelines and inflate wages across all sectors',
    mechanism: 'Demand for 500k homes in 3 years requires ~180k additional tradespeople. Toronto (unemployment 6.7%, 5,146 starts/yr) and Vancouver (vacancy 0.9%) already face severe shortages. Bidding wars for workers will push residential wages 20–35% above market, crowding out infrastructure projects.',
    severity: 3,
    category: 'employment',
    most_exposed: 'Construction workers, salaried tradespeople, and municipalities running parallel infrastructure projects',
    cities_most_affected: ['Toronto', 'Vancouver', 'Calgary'],
  },
  {
    source: 'urban_planner',
    risk: 'Rapid densification will overwhelm transit, schools, and utility infrastructure in growth corridors',
    mechanism: 'New developments will be approved faster than supporting infrastructure can be built. Cities like Montreal (pop growth 1.8%/yr) and Ottawa lack capacity to upgrade water/sewer lines within the build window, creating service failures within 5 years of occupancy.',
    severity: 3,
    category: 'infrastructure',
    most_exposed: 'New homebuyers and renters in high-growth suburban corridors',
    cities_most_affected: ['Montreal', 'Ottawa', 'Kitchener-Waterloo'],
  },
  {
    source: 'fiscal_analyst',
    risk: 'Municipal tax bases will be stressed by infrastructure servicing obligations before new units generate revenue',
    mechanism: 'Development charge deferrals and front-loaded servicing costs create a 7–10 year lag before new units contribute net tax revenue. Cities like Halifax (pop 450k, low industrial base) face structural deficits if forced to finance servicing at scale.',
    severity: 2,
    category: 'fiscal',
    most_exposed: 'Existing property taxpayers and municipalities with thin credit margins',
    cities_most_affected: ['Halifax', 'Winnipeg', 'Regina'],
  },
  {
    source: 'housing_economist',
    risk: 'Speculative pre-construction demand will inflate land prices faster than supply can suppress them',
    mechanism: 'Announcement of large-scale supply targets historically triggers land speculation. In Toronto (avg rent 1BR $2,400, vacancy 1.1%) and Vancouver, developers will front-load land acquisition, pushing lot prices up 15–25% within 12 months and absorbing affordability gains.',
    severity: 3,
    category: 'affordability',
    most_exposed: 'First-time buyers and renters in high-demand urban markets',
    cities_most_affected: ['Toronto', 'Vancouver'],
  },
  {
    source: 'social_equity_researcher',
    risk: 'Low-income renters will face displacement as new developments trigger neighbourhood gentrification',
    mechanism: 'Supply-side investment tends to cluster in high-ROI areas, accelerating gentrification in adjacent low-income neighbourhoods. In Montreal (63% renter rate, median household income $58k) and Hamilton, renters on fixed incomes face 18–24 month displacement timelines as rents rise ahead of new supply arriving.',
    severity: 2,
    category: 'displacement',
    most_exposed: 'Low-income renters, recent immigrants, and seniors in legacy rental stock',
    cities_most_affected: ['Montreal', 'Hamilton', 'Toronto'],
  },
  {
    source: 'regional_development_analyst',
    risk: 'Rural and Indigenous communities will be bypassed, deepening the urban-rural housing gap',
    mechanism: 'Private developers will concentrate builds where returns are highest. Communities in Northern Ontario, Nunavut, and rural Saskatchewan lack the density economics to attract private capital. Federal resources directed at urban targets will leave rural affordable-housing deficits unaddressed.',
    severity: 2,
    category: 'geographic',
    most_exposed: 'Rural residents, Indigenous communities, and remote workers',
    cities_most_affected: ['Saskatoon', 'Regina', 'Northern Ontario Rural'],
  },
  {
    source: 'construction_industry_analyst',
    risk: 'Rapid scaling of build volume will produce widespread building quality deficiencies',
    mechanism: 'Contractor capacity constraints and accelerated permitting will reduce inspection frequency. Historical precedents (Ontario condo boom 2012–2018) show defect rates triple when annual starts exceed industry absorption capacity. With 167k homes/year targeted nationally vs. ~240k current capacity, quality oversight will fail in 30–40% of units.',
    severity: 2,
    category: 'infrastructure',
    most_exposed: 'New homebuyers purchasing at peak volume, particularly first-time buyers with limited ability to absorb repair costs',
    cities_most_affected: ['Toronto', 'Calgary', 'Edmonton'],
  },
  {
    source: 'demographic_economist',
    risk: 'Supply targets assume stable immigration rates; demand shocks could render the 500k figure insufficient within 18 months',
    mechanism: 'Canada\'s current 500k/yr immigration intake adds ~180k new households annually. If policy triggers a pull-factor migration surge of 10–15%, the 500k unit target could be absorbed in 2 years, not 3, leaving a structural deficit. Vacancy rates in Toronto (1.1%) and Vancouver (0.9%) give no buffer.',
    severity: 2,
    category: 'affordability',
    most_exposed: 'Recent immigrants, young renters, and households in high-demand cities',
    cities_most_affected: ['Toronto', 'Vancouver', 'Calgary'],
  },
];

// ── Validators ───────────────────────────────────────────────────────────────

const CITIES = ['Toronto', 'Vancouver', 'Montreal', 'Calgary', 'Halifax', 'Winnipeg', 'Ottawa', 'Hamilton', 'Saskatoon'];
const TENURES: ('renter' | 'owner')[] = ['renter', 'owner'];
const AGES = ['18-24', '25-34', '35-49', '50-64', '65+'];
const INCOMES = ['very_low', 'low', 'medium', 'high', 'very_high'];
const IMMIGRATION = ['born_here', 'established_immigrant', 'recent_immigrant'];
const FAMILY = ['single', 'couple', 'small_family', 'large_family'];
const EMPLOYMENT = ['salaried', 'gig', 'self_employed', 'student', 'retired'];

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

const MISSED_RISK_POOL = [
  { risk: 'Increased difficulty accessing affordable housing due to high competition from investors', category: 'affordability', severity: 3 as const },
  { risk: 'Shortage of accessible housing for people with disabilities in new builds', category: 'equity', severity: 2 as const },
  { risk: 'Construction noise and disruption will lower quality of life in existing dense neighbourhoods', category: 'infrastructure', severity: 1 as const },
  { risk: 'New housing stock may not be culturally appropriate for multi-generational immigrant families', category: 'equity', severity: 2 as const },
  { risk: 'Increased rental competition from well-capitalised investors will price out low-income renters', category: 'affordability', severity: 3 as const },
  { risk: 'Remote and hybrid workers may flood smaller markets, displacing long-term local residents', category: 'displacement', severity: 2 as const },
  { risk: 'Fixed-income seniors face property tax increases triggered by rising assessed values', category: 'fiscal', severity: 2 as const },
  { risk: 'Gig and contract workers will be excluded from mortgage qualification despite earning capacity', category: 'affordability', severity: 2 as const },
];

function generateValidators(count: number): ValidatorResult[] {
  return Array.from({ length: count }).map((_, i) => {
    const numValidations = SPECIALIST_RISKS.length;
    // Each validator confirms a random subset of risks
    const validations = Array.from({ length: numValidations }).map((__, rIdx) => {
      const applies = Math.random() > 0.35;
      const sev = applies ? (pick([1, 2, 3]) as 0 | 1 | 2 | 3) : 0;
      return {
        risk_index: rIdx + 1,
        applies,
        severity_for_me: sev,
        reason: applies
          ? pick([
              'This directly affects my housing cost burden given local rent levels.',
              'As a renter in a high-demand city, this risk compounds my existing vulnerability.',
              'My income bracket means I have no buffer against these cost increases.',
              'Working in construction I would feel this through wage and workload pressure.',
              'My neighbourhood is already under gentrification pressure; this accelerates it.',
              'As a recent immigrant, I have fewer options if this squeezes the rental market.',
              'This affects the infrastructure my family relies on daily.',
            ])
          : 'My ownership status and income level insulate me from this particular risk.',
      };
    });

    const missed = Math.random() > 0.6 ? pick(MISSED_RISK_POOL) : null;

    return {
      agent_id: i + 1,
      city: pick(CITIES),
      tenure: pick(TENURES),
      age_bracket: pick(AGES),
      income_bracket: pick(INCOMES),
      immigration_status: pick(IMMIGRATION),
      family_size: pick(FAMILY),
      employment_type: pick(EMPLOYMENT),
      population_weight: 0.03,
      validations,
      missed_risk: missed,
    };
  });
}

// ── Full mock output ──────────────────────────────────────────────────────────

export const MOCK_SIMULATION_OUTPUT: SimulationOutput = {
  policy: 'Canada builds 500,000 new homes over 3 years',
  total_time_seconds: 62.4,
  specialists_total: 8,
  validators_total: 34,
  models: {
    specialist: 'openai/gpt-4o',
    validator: 'anthropic/claude-3-haiku-20240307',
    coordinator: 'openai/gpt-4o',
  },
  round_1_specialists: [
    { specialist: 'labor_economist', risks: [SPECIALIST_RISKS[0]] },
    { specialist: 'urban_planner', risks: [SPECIALIST_RISKS[1]] },
    { specialist: 'fiscal_analyst', risks: [SPECIALIST_RISKS[2]] },
    { specialist: 'housing_economist', risks: [SPECIALIST_RISKS[3]] },
    { specialist: 'social_equity_researcher', risks: [SPECIALIST_RISKS[4]] },
    { specialist: 'regional_development_analyst', risks: [SPECIALIST_RISKS[5]] },
    { specialist: 'construction_industry_analyst', risks: [SPECIALIST_RISKS[6]] },
    { specialist: 'demographic_economist', risks: [SPECIALIST_RISKS[7]] },
  ],
  specialist_risks: SPECIALIST_RISKS,
  round_2_validators: generateValidators(34),
  risk_report: {
    risks: [
      {
        rank: 1,
        title: 'Construction labour shortage stalls timeline and raises costs',
        severity: 'HIGH',
        reasoning: 'The policy\'s 3-year timeline requires nearly doubling current construction output. Labour markets in Toronto and Vancouver are already at capacity, and a surge demand will trigger wage inflation that cascades into all sectors. 31 of 34 validators confirmed this affects them through higher housing costs or direct employment impacts.',
        affected_groups: 'Renters and prospective buyers in urban centres; existing tradespeople',
        confirmed_by: 31,
        out_of: 34,
        cities: ['Toronto', 'Vancouver', 'Calgary'],
        cascade_effect: 'Wage inflation in construction bleeds into all infrastructure projects, delaying transit and utilities needed to service the new housing.',
      },
      {
        rank: 2,
        title: 'Speculative land acquisition absorbs affordability gains',
        severity: 'HIGH',
        reasoning: 'Announcement effects in Toronto and Vancouver markets historically trigger rapid land price escalation. Developers acquiring land ahead of rezoning will capture value that should accrue to buyers. 26 validators confirmed, concentrated among low-to-medium income renters in high-demand cities.',
        affected_groups: 'First-time buyers, low-income renters in urban markets',
        confirmed_by: 26,
        out_of: 34,
        cities: ['Toronto', 'Vancouver'],
        cascade_effect: 'Higher land costs reduce unit mix viability for affordable housing, shifting builds toward market-rate product only.',
      },
      {
        rank: 3,
        title: 'Infrastructure capacity lag creates service failures in new communities',
        severity: 'MEDIUM',
        reasoning: 'Schools, transit, and utilities cannot be built fast enough to service rapid densification. Confirmed by 22 validators, especially families in suburban growth areas relying on schools and transit.',
        affected_groups: 'Families in new developments, suburban renters',
        confirmed_by: 22,
        out_of: 34,
        cities: ['Montreal', 'Ottawa', 'Kitchener-Waterloo'],
        cascade_effect: null,
      },
      {
        rank: 4,
        title: 'Displacement of low-income renters through gentrification pressure',
        severity: 'MEDIUM',
        reasoning: 'Investment clustering in high-ROI zones accelerates rent increases in adjacent low-income neighbourhoods ahead of new supply arriving. Confirmed by 18 validators, primarily low-income renters in Montreal and Hamilton.',
        affected_groups: 'Low-income renters, recent immigrants, seniors',
        confirmed_by: 18,
        out_of: 34,
        cities: ['Montreal', 'Hamilton', 'Toronto'],
        cascade_effect: 'Displaced renters move to outer rings, increasing commute distances and transport costs.',
      },
      {
        rank: 5,
        title: 'Rural and Indigenous communities bypassed by private capital',
        severity: 'LOW',
        reasoning: 'Private developers will not build in markets lacking density economics. Rural Saskatchewan and Northern Ontario communities confirmed this, but only 9 validators—reflecting underrepresentation of rural demographics.',
        affected_groups: 'Rural residents, Indigenous communities',
        confirmed_by: 9,
        out_of: 34,
        cities: ['Saskatoon', 'Northern Ontario Rural'],
        cascade_effect: null,
      },
    ],
    blind_spots: 'Rural, Indigenous, and northern remote demographics are underrepresented in the 34-agent panel.',
    overall_risk_level: 'HIGH',
    key_insight: 'The policy\'s affordability benefits will be captured by land speculators and offset by construction wage inflation before a single unit reaches a low-income buyer.',
  },
  confidence: {
    score: 8,
    out_of: 10,
    reason: 'strong StatsCan data coverage for this policy type; all validators responded successfully',
    caveat: 'This is a hypothesis generation tool. Findings should be validated against real survey data before informing policy decisions.',
  },
  policy_classification: {
    type: 'supply',
    primary_affected: 'renters, first-time buyers',
    market: 'housing',
    geography: 'national',
    time_horizon: 'medium_term',
    key_attributes: ['tenure', 'income', 'city'],
  },
  seal_id: 'mock-a1b2c3d4',
};
