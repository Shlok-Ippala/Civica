import { createRoot } from 'react-dom/client'
import React from 'react'
import './index.css'
import App from './App.tsx'

class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { error: Error | null }
> {
  state = { error: null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: '4rem', fontFamily: 'monospace', color: '#ff2a00' }}>
          <div style={{ marginBottom: '1rem', fontSize: '1.2rem' }}>RUNTIME ERROR</div>
          <pre style={{ whiteSpace: 'pre-wrap', color: '#ebe8e0', fontSize: '0.85rem' }}>
            {(this.state.error as Error).message}
            {'\n\n'}
            {(this.state.error as Error).stack}
          </pre>
          <button
            onClick={() => this.setState({ error: null })}
            style={{ marginTop: '2rem', padding: '0.5rem 1.5rem', border: '1px solid #ff2a00', color: '#ff2a00', background: 'none', cursor: 'pointer', fontFamily: 'monospace' }}
          >
            [ RELOAD ]
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById('root')!).render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>,
)
