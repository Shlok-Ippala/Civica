import React, { useState } from 'react';
import { motion } from 'framer-motion';
import type { SimulationOutput, SpecialistRisk, ValidatorResult } from '../types';
import './Stage3.css';

const SPECIALIST_LABELS: Record<string, string> = {
  labor_economist: 'Labor Economist',
  urban_planner: 'Urban Planner',
  fiscal_analyst: 'Fiscal Analyst',
  housing_economist: 'Housing Economist',
  social_equity_researcher: 'Equity Researcher',
  regional_development_analyst: 'Regional Analyst',
  construction_industry_analyst: 'Construction Analyst',
  demographic_economist: 'Demographic Economist',
};

// ── Helpers ──────────────────────────────────────────────────────────────────

function severityColor(sev: number | string): string {
  if (sev === 3 || sev === 'HIGH') return 'var(--signal-negative)';
  if (sev === 2 || sev === 'MEDIUM') return 'var(--signal-mixed)';
  return 'var(--signal-positive)';
}

function severityLabel(sev: number): string {
  return sev === 3 ? 'HIGH' : sev === 2 ? 'MED' : 'LOW';
}

function getConfirmingValidators(validators: ValidatorResult[], riskIndex: number) {
  return validators.filter(v =>
    v.validations.some(val => val.risk_index === riskIndex && val.applies)
  );
}

function getTopValidationForAgent(v: ValidatorResult) {
  return v.validations
    .filter(val => val.applies && val.severity_for_me > 0)
    .sort((a, b) => b.severity_for_me - a.severity_for_me)[0] ?? null;
}

// ── Specialist Risk Card ──────────────────────────────────────────────────────

interface RiskCardProps {
  risk: SpecialistRisk;
  riskIndex: number;
  validators: ValidatorResult[];
}

const SpecialistRiskCard: React.FC<RiskCardProps> = ({ risk, riskIndex, validators }) => {
  const [expanded, setExpanded] = useState(false);

  const confirming = getConfirmingValidators(validators, riskIndex);
  const total = validators.length;
  const pct = total > 0 ? (confirming.length / total) * 100 : 0;

  const byTenure: Record<string, number> = {};
  const byAge: Record<string, number> = {};
  const byIncome: Record<string, number> = {};
  for (const v of confirming) {
    byTenure[v.tenure] = (byTenure[v.tenure] || 0) + 1;
    byAge[v.age_bracket] = (byAge[v.age_bracket] || 0) + 1;
    byIncome[v.income_bracket] = (byIncome[v.income_bracket] || 0) + 1;
  }
  const topAges = Object.entries(byAge).sort((a, b) => b[1] - a[1]).slice(0, 2);
  const topIncome = Object.entries(byIncome).sort((a, b) => b[1] - a[1])[0];

  const topForAgents = validators.filter(v => {
    const top = getTopValidationForAgent(v);
    return top?.risk_index === riskIndex;
  });

  const topConfirmations = confirming
    .map(v => ({
      v,
      val: v.validations.find(val => val.risk_index === riskIndex && val.applies)!,
    }))
    .sort((a, b) => b.val.severity_for_me - a.val.severity_for_me)
    .slice(0, 3);

  const color = severityColor(risk.severity);

  return (
    <div className="risk-card" style={{ borderLeftColor: color }}>
      <div className="risk-card-header">
        <div className="risk-card-badges">
          <span className="badge-specialist">
            {SPECIALIST_LABELS[risk.source] || risk.source}
          </span>
          <span className="badge-category">{risk.category}</span>
          <span className="badge-severity" style={{ color }}>
            {severityLabel(risk.severity)}
          </span>
        </div>
        <button className="btn-expand" onClick={() => setExpanded(e => !e)}>
          [{expanded ? '−' : '+'}]
        </button>
      </div>

      <p className="risk-card-text">{risk.risk}</p>

      <div className="agreement-section">
        <div className="agreement-label">
          <span>AGENT AGREEMENT</span>
          <span style={{ color }}>{confirming.length}/{total} agents</span>
        </div>
        <div className="agreement-bar-track">
          <div
            className="agreement-bar-fill"
            style={{ width: `${pct}%`, backgroundColor: color }}
          />
        </div>
      </div>

      <div className="demo-row">
        <span className="demo-chip">{byTenure['renter'] ?? 0} renters</span>
        <span className="demo-chip">{byTenure['owner'] ?? 0} owners</span>
        {topAges.map(([age, count]) => (
          <span key={age} className="demo-chip">{count}× {age}</span>
        ))}
        {topIncome && (
          <span className="demo-chip">{topIncome[1]}× {topIncome[0]} income</span>
        )}
      </div>

      {topForAgents.length > 0 && (
        <div className="top-for-section">
          <span className="top-for-label">
            TOP PRIORITY FOR {topForAgents.length} AGENT{topForAgents.length !== 1 ? 'S' : ''}:
          </span>
          <div className="top-for-agents">
            {topForAgents.slice(0, 7).map(v => (
              <span key={v.agent_id} className="top-for-chip">
                [{v.agent_id.toString().padStart(2, '0')}] {v.city.substring(0, 3).toUpperCase()} {v.tenure}/{v.age_bracket}
              </span>
            ))}
            {topForAgents.length > 7 && (
              <span className="top-for-chip dimmed">+{topForAgents.length - 7} more</span>
            )}
          </div>
        </div>
      )}

      {expanded && (
        <div className="risk-card-expanded">
          <div className="mechanism-block">
            <span className="mechanism-label">MECHANISM</span>
            <p className="mechanism-text">{risk.mechanism}</p>
          </div>

          {risk.most_exposed && (
            <div className="mechanism-block">
              <span className="mechanism-label">MOST EXPOSED</span>
              <p className="mechanism-text">{risk.most_exposed}</p>
            </div>
          )}

          {risk.cities_most_affected.length > 0 && (
            <div className="mechanism-block">
              <span className="mechanism-label">CITIES AFFECTED</span>
              <div className="cities-list">
                {risk.cities_most_affected.map(c => (
                  <span key={c} className="city-chip">{c}</span>
                ))}
              </div>
            </div>
          )}

          {topConfirmations.length > 0 && (
            <div className="mechanism-block">
              <span className="mechanism-label">AGENT VOICES</span>
              {topConfirmations.map(({ v, val }) => (
                <div key={v.agent_id} className="confirmation-entry">
                  <span className="conf-agent">
                    [{v.agent_id.toString().padStart(2, '0')}] {v.city} · {v.tenure} · {v.age_bracket} · {v.income_bracket}
                  </span>
                  <span className="conf-reason">"{val.reason}"</span>
                  <span className="conf-sev" style={{ color: severityColor(val.severity_for_me) }}>
                    severity {val.severity_for_me}/3
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ── Main Stage3 ───────────────────────────────────────────────────────────────

interface Props {
  data: SimulationOutput;
  onRestart: () => void;
}

export const Stage3Findings: React.FC<Props> = ({ data, onRestart }) => {
  const { risk_report, round_2_validators, specialist_risks } = data;

  const riskLevelColor = severityColor(risk_report.overall_risk_level);

  const agentTopRisks = round_2_validators.map(v => {
    const top = getTopValidationForAgent(v);
    const topRisk = top ? specialist_risks[top.risk_index - 1] : null;
    return { validator: v, topValidation: top, topRisk };
  });

  const personaRisks = round_2_validators.filter(v => v.missed_risk != null);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 1, transition: { duration: 0 } }}
      transition={{ duration: 0.3 }}
      className="stage3-container"
    >
      <div className="stage3-inner">
      {/* ── Header ── */}
      <header className="report-header">
        <div className="report-meta">
          <span>CLASSIFIED INTELLIGENCE REPORT</span>
          <span>SEAL: {data.seal_id || '—'}</span>
        </div>
        <div className="report-policy">
          <h2>POLICY DIRECTIVE</h2>
          <p>{data.policy}</p>
        </div>
      </header>

      <div className="report-body">

        {/* ── Intelligence Summary ── */}
        <section className="section-summary">
          <h4>INTELLIGENCE SUMMARY</h4>
          <div className="summary-meta-row">
            <div className="summary-stat">
              <span className="summary-label">OVERALL RISK</span>
              <span className="risk-level-badge" style={{ color: riskLevelColor, borderColor: riskLevelColor }}>
                {risk_report.overall_risk_level}
              </span>
            </div>
            {data.confidence && (
              <div className="summary-stat">
                <span className="summary-label">CONFIDENCE</span>
                <span className="summary-value">{data.confidence.score}/{data.confidence.out_of}</span>
              </div>
            )}
            <div className="summary-stat">
              <span className="summary-label">SPECIALISTS</span>
              <span className="summary-value">{data.specialists_total}</span>
            </div>
            <div className="summary-stat">
              <span className="summary-label">VALIDATORS</span>
              <span className="summary-value">{data.validators_total}</span>
            </div>
          </div>

          <h1 className="emergent-headline">{risk_report.key_insight}</h1>

          {risk_report.blind_spots && (
            <p className="blind-spots-note">
              <span className="blind-label">BLIND SPOTS —</span> {risk_report.blind_spots}
            </p>
          )}
          {data.confidence && (
            <p className="caveat-note">{data.confidence.caveat}</p>
          )}
        </section>

        {/* ── Specialist Risk Assessment ── */}
        <section className="section-specialist-risks">
          <h4>
            SPECIALIST RISK ASSESSMENT — {specialist_risks.length} RISKS IDENTIFIED · CLICK TO EXPAND
          </h4>
          <div className="risk-cards-list">
            {specialist_risks.map((risk, i) => (
              <SpecialistRiskCard
                key={i}
                risk={risk}
                riskIndex={i + 1}
                validators={round_2_validators}
              />
            ))}
          </div>
        </section>

        {/* ── Agent Top Priorities ── */}
        <section className="section-agent-priorities">
          <h4>AGENT TOP PRIORITIES — WHAT EACH VALIDATOR RANKED MOST CRITICAL</h4>
          <div className="archive-strip">
            {agentTopRisks.map(({ validator: v, topValidation, topRisk }) => (
              <div key={v.agent_id} className="priority-card">
                <div className="a-id">
                  [{v.agent_id.toString().padStart(2, '0')}] {v.city.substring(0, 3).toUpperCase()}
                </div>
                <div className="a-demo">{v.tenure} / {v.age_bracket} / {v.income_bracket}</div>

                {topRisk && topValidation ? (
                  <>
                    <div
                      className="a-priority-risk"
                      style={{ borderLeft: `2px solid ${severityColor(topValidation.severity_for_me)}` }}
                    >
                      {topRisk.risk.length > 80 ? topRisk.risk.substring(0, 80) + '…' : topRisk.risk}
                    </div>
                    <div className="a-sev-dots">
                      {[1, 2, 3].map(n => (
                        <span
                          key={n}
                          className="sev-dot"
                          style={{
                            backgroundColor: n <= topValidation.severity_for_me
                              ? severityColor(topValidation.severity_for_me)
                              : 'var(--border-sharp)',
                          }}
                        />
                      ))}
                    </div>
                    <div className="a-reason">
                      "{topValidation.reason.substring(0, 70)}{topValidation.reason.length > 70 ? '…' : ''}"
                    </div>
                  </>
                ) : (
                  <div className="a-no-priority">no risks confirmed</div>
                )}

                {v.missed_risk && (
                  <div className="a-proposed-badge">+ proposed own risk</div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* ── Persona-Generated Risks ── */}
        {personaRisks.length > 0 && (
          <section className="section-persona-risks">
            <h4>
              PERSONA-GENERATED RISKS — {personaRisks.length} RISKS FLAGGED BY VALIDATORS
            </h4>
            <p className="section-subheader">
              Risks identified by demographic personas that specialists did not surface
            </p>
            <div className="persona-risk-grid">
              {personaRisks.map(v => (
                <div key={v.agent_id} className="persona-risk-card">
                  <div className="persona-agent-header">
                    <span className="prc-id">[{v.agent_id.toString().padStart(2, '0')}]</span>
                    <span className="prc-city">{v.city}</span>
                    <span className="prc-demo">{v.tenure} · {v.age_bracket} · {v.income_bracket}</span>
                  </div>
                  <p className="prc-risk">"{v.missed_risk!.risk}"</p>
                  <div className="prc-footer">
                    <span className="badge-category">{v.missed_risk!.category}</span>
                    <span
                      className="badge-severity"
                      style={{ color: severityColor(v.missed_risk!.severity) }}
                    >
                      {severityLabel(v.missed_risk!.severity)}
                    </span>
                    <span className="prc-employment">{v.employment_type}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        <button className="btn-restart" onClick={onRestart}>
          [ INITIALIZE NEW SIMULATION ]
        </button>
      </div>
      </div>
    </motion.div>
  );
};
