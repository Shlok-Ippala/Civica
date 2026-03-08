import { useState, useRef } from 'react';
import { AnimatePresence } from 'framer-motion';

import { Stage1Input } from './components/Stage1Input';
import { Stage2Simulation } from './components/Stage2Simulation';
import { Stage3Findings } from './components/Stage3Findings';
import type { AnimationEntry, SimulationEvent, SimulationOutput, SpecialistResult, ValidatorResult } from './types';
import './App.css';

const API_BASE = 'http://localhost:8000';

type Stage = 'INPUT' | 'SIMULATION_R1' | 'SIMULATION_R2' | 'FINDINGS';

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

function specialistsToEntries(specialists: SpecialistResult[]): AnimationEntry[] {
  return specialists.filter(Boolean).map((s, i) => {
    const topRisk = [...s.risks].sort((a, b) => b.severity - a.severity)[0];
    const signal: AnimationEntry['signal'] = topRisk
      ? topRisk.severity === 3 ? 'negative' : topRisk.severity === 2 ? 'mixed' : 'positive'
      : 'mixed';
    return {
      id: i + 1,
      label: SPECIALIST_LABELS[s.specialist] || s.specialist,
      sublabel: topRisk?.category ?? 'analysis',
      concern: topRisk?.risk?.substring(0, 90) ?? 'analysis complete',
      signal,
    };
  });
}

function validatorsToEntries(validators: ValidatorResult[]): AnimationEntry[] {
  return validators.filter(Boolean).map(v => {
    const confirmed = v.validations.filter(val => val.applies).length;
    const total = v.validations.length;
    const ratio = total > 0 ? confirmed / total : 0;
    const signal: AnimationEntry['signal'] = ratio > 0.6 ? 'negative' : ratio > 0.3 ? 'mixed' : 'positive';
    return {
      id: v.agent_id,
      label: v.city.substring(0, 3).toUpperCase(),
      sublabel: `${v.tenure} / ${v.age_bracket}`,
      concern: v.missed_risk?.risk?.substring(0, 90) ?? 'validation complete',
      signal,
    };
  });
}

function App() {
  const [stage, setStage] = useState<Stage>('INPUT');
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [error, setError] = useState('');

  const [r1Entries, setR1Entries] = useState<AnimationEntry[]>([]);
  const [r2Entries, setR2Entries] = useState<AnimationEntry[]>([]);
  const [r2Ready, setR2Ready] = useState(false);
  const [doneReady, setDoneReady] = useState(false);
  const [simulationData, setSimulationData] = useState<SimulationOutput | null>(null);

  const policyRef = useRef('');

  const handlePolicySubmit = async (policy: string) => {
    policyRef.current = policy;
    setLoading(true);
    setError('');
    setStatusMessage('Connecting...');
    setR2Ready(false);
    setDoneReady(false);
    setSimulationData(null);

    try {
      const response = await fetch(`${API_BASE}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ policy }),
      });

      if (response.status === 422) {
        const body = await response.json();
        throw new Error(body.error ?? 'Invalid policy input.');
      }
      if (!response.ok) throw new Error(`Server error: ${response.status}`);
      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;

          let event: SimulationEvent;
          try {
            event = JSON.parse(raw);
          } catch {
            continue;
          }

          if (event.type === 'status') {
            setStatusMessage(event.message);
          } else if (event.type === 'r1_complete') {
            setR1Entries(specialistsToEntries(event.specialists));
            setLoading(false);
            setStage('SIMULATION_R1');
          } else if (event.type === 'r2_complete') {
            setR2Entries(validatorsToEntries(event.validators));
            setR2Ready(true);
          } else if (event.type === 'done') {
            setSimulationData(event.data);
            setDoneReady(true);
          } else if (event.type === 'error') {
            setError(event.message);
            setLoading(false);
            setStage('INPUT');
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setLoading(false);
      setStage('INPUT');
    }
  };

  const handleR1Complete = () => {
    setStage('SIMULATION_R2');
  };

  const handleR2Complete = () => {
    if (simulationData) {
      setStage('FINDINGS');
    }
    // If data not yet ready, doneReady effect will trigger once it arrives
  };

  // If R2 animation completes before done event, transition as soon as data arrives
  const handleRestart = () => {
    setStage('INPUT');
    setSimulationData(null);
    setR1Entries([]);
    setR2Entries([]);
    setR2Ready(false);
    setDoneReady(false);
    setError('');
    setStatusMessage('');
  };

  return (
    <div className="app-container">
      <AnimatePresence mode="sync">
        {stage === 'INPUT' && (
          <Stage1Input
            key="stage1"
            onSubmit={handlePolicySubmit}
            loading={loading}
            statusMessage={statusMessage}
            error={error}
          />
        )}

        {stage === 'SIMULATION_R1' && (
          <Stage2Simulation
            key="stage2-r1"
            entries={r1Entries}
            roundNum={1}
            roundLabel="SPECIALIST ANALYSIS"
            canAdvance={r2Ready}
            onComplete={handleR1Complete}
          />
        )}

        {stage === 'SIMULATION_R2' && (
          <Stage2Simulation
            key="stage2-r2"
            entries={r2Entries}
            roundNum={2}
            roundLabel="DEMOGRAPHIC VALIDATION"
            canAdvance={doneReady}
            onComplete={handleR2Complete}
          />
        )}

        {stage === 'FINDINGS' && simulationData && (
          <Stage3Findings
            key="stage3"
            data={simulationData}
            onRestart={handleRestart}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
