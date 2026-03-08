import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface Props {
  onSubmit: (policy: string) => void;
  loading?: boolean;
  statusMessage?: string;
  error?: string;
}

export const Stage1Input: React.FC<Props> = ({ onSubmit, loading = false, statusMessage, error }) => {
  const [policy, setPolicy] = useState('');

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (policy.trim() && !loading) {
        onSubmit(policy.trim());
      }
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 1, transition: { duration: 0 } }}
      transition={{ duration: 0.3 }}
      className="stage1-container"
    >
      <div className="meta-timestamp left-top">SYS_TIME: {new Date().toISOString()}</div>
      <div className="meta-stamp right-top">SPECIALISTS: 8 | VALIDATORS: 50</div>

      <div className="center-content">
        <motion.h1
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="prompt-header"
        >
          {loading ? 'INITIALIZING' : 'ENTER POLICY'}
        </motion.h1>

        {!loading && (
          <motion.div
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ delay: 0.4, duration: 0.5 }}
            className="input-wrapper"
          >
            <span className="caret">{'>_'}</span>
            <textarea
              autoFocus
              value={policy}
              onChange={(e) => setPolicy(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Awaiting directive..."
              rows={3}
              spellCheck={false}
            />
          </motion.div>
        )}

        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="loading-block"
          >
            <div className="loading-policy">"{policy}"</div>
            <div className="loading-status blink">
              {statusMessage || 'CONNECTING TO BACKBOARD...'}
            </div>
            <div className="loading-bar">
              <div className="loading-bar-fill" />
            </div>
          </motion.div>
        )}

        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="error-block"
          >
            <span className="error-label">ERROR —</span> {error}
            <button className="btn-retry" onClick={() => onSubmit(policy)}>[ RETRY ]</button>
          </motion.div>
        )}

        {!loading && !error && (
          <div className="submit-hint">ENTER to submit · SHIFT+ENTER for new line</div>
        )}
      </div>

      <div className="meta-stamp left-bottom">VER: 2.0.0-PROD</div>
      <div className="meta-stamp right-bottom">SCOPE: NATIONAL</div>
    </motion.div>
  );
};
