import React, { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import type { AnimationEntry } from '../types';
import './Stage2.css';

interface Props {
  entries: AnimationEntry[];
  onComplete: () => void;
  roundNum: number;
  roundLabel: string;
  canAdvance: boolean;
}

export const Stage2Simulation: React.FC<Props> = ({ entries, onComplete, roundNum, roundLabel, canAdvance }) => {
  const [activeEntries, setActiveEntries] = useState<AnimationEntry[]>([]);
  const [animationDone, setAnimationDone] = useState(false);
  const logFeedRef = useRef<HTMLDivElement>(null);
  const completedRef = useRef(false);

  // Reset when entries change
  useEffect(() => {
    setActiveEntries([]);
    setAnimationDone(false);
    completedRef.current = false;
  }, [entries]);

  // Stream entries in one by one
  useEffect(() => {
    if (entries.length === 0) return;
    let currentIndex = 0;
    let isCancelled = false;

    // R1 has few entries (specialists) — spread them out so they're visible
    // R2 has many entries (validators) — faster stream is fine
    const intervalMs = entries.length <= 10 ? 800 : 150;

    const interval = setInterval(() => {
      if (isCancelled) return;
      if (currentIndex < entries.length) {
        const entryToAdd = entries[currentIndex];
        currentIndex++;
        if (!entryToAdd) return;
        setActiveEntries(prev => {
          if (prev.length >= entries.length) return prev;
          return [...prev, entryToAdd];
        });
      } else {
        clearInterval(interval);
        setAnimationDone(true);
      }
    }, intervalMs);

    return () => {
      isCancelled = true;
      clearInterval(interval);
    };
  }, [entries]);

  // Advance only when BOTH animation is done AND backend signals ready
  useEffect(() => {
    if (animationDone && canAdvance && !completedRef.current) {
      completedRef.current = true;
      setTimeout(onComplete, 800);
    }
  }, [animationDone, canAdvance, onComplete]);

  // Auto-scroll log
  useEffect(() => {
    if (logFeedRef.current) {
      logFeedRef.current.scrollTop = logFeedRef.current.scrollHeight;
    }
  }, [activeEntries]);

  const getSignalColor = (signal: AnimationEntry['signal']) => {
    switch (signal) {
      case 'positive': return 'var(--signal-positive)';
      case 'negative': return 'var(--signal-negative)';
      default: return 'var(--signal-mixed)';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 1, transition: { duration: 0 } }}
      transition={{ duration: 0.3 }}
      className="stage2-container"
    >
      <div className="status-header">
        <div className="status-item">
          <span className="label">STATE</span>
          <span className="value blink">SIMULATION RUNNING</span>
        </div>
        <div className="status-item">
          <span className="label">ROUND</span>
          <span className="value">{roundNum} OF 2 — {roundLabel}</span>
        </div>
        <div className="status-item">
          <span className="label">RESPONSES</span>
          <span className="value">{activeEntries.length} / {entries.length}</span>
        </div>
        <div className="status-item">
          <span className="label">BACKEND</span>
          <span className="value" style={{ color: canAdvance ? 'var(--signal-positive)' : 'var(--signal-mixed)' }}>
            {canAdvance ? 'READY' : 'PROCESSING'}
          </span>
        </div>
      </div>

      <div className="chamber-layout">
        <div className="agent-grid">
          {entries.filter(Boolean).map((entry, i) => {
            const isActive = i < activeEntries.length;
            const signal = isActive ? getSignalColor(entry.signal) : 'transparent';
            return (
              <div
                key={entry.id}
                className={`agent-card ${isActive ? 'active' : 'idle'}`}
                style={{ '--signal': signal } as React.CSSProperties}
              >
                {isActive && (
                  <>
                    <div className="agent-geo">{entry.label.substring(0, 3).toUpperCase()}</div>
                    <div className="agent-signal" style={{ backgroundColor: signal }}></div>
                  </>
                )}
              </div>
            );
          })}
        </div>

        <div className="live-log-container">
          <div className="log-header">LIVE INTELLIGENCE FEED</div>
          <div className="log-feed" ref={logFeedRef}>
            {activeEntries.filter(Boolean).map(entry => (
              <div key={entry.id} className="log-entry">
                <span className="log-id">[{entry.id.toString().padStart(2, '0')}]</span>
                <span className="log-geo">{entry.label.toUpperCase()}</span>
                <span className="log-demo">{entry.sublabel}</span>
                <span className="log-sentiment" style={{ color: getSignalColor(entry.signal) }}>
                  {entry.signal === 'negative' ? 'HIGH' : entry.signal === 'mixed' ? 'MED' : 'LOW'}
                </span>
                <span className="log-concern">"{entry.concern}"</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
};
