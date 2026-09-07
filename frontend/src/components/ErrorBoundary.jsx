import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null, showDetails: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("QUANTA Engine caught an unhandled UI error:", error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReload = () => {
    window.location.reload();
  };

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null, showDetails: false });
  };

  toggleDetails = () => {
    this.setState(prev => ({ showDetails: !prev.showDetails }));
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          backgroundColor: '#0B1020',
          color: '#F8FAFC',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px',
          textAlign: 'center',
          fontFamily: 'Inter, system-ui, sans-serif'
        }}>
          <div style={{
            maxWidth: '560px',
            width: '100%',
            background: 'rgba(15, 23, 42, 0.95)',
            border: '1px solid rgba(0, 240, 255, 0.35)',
            borderRadius: '16px',
            padding: '32px',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6), 0 0 30px rgba(0, 240, 255, 0.15)',
            backdropFilter: 'blur(16px)'
          }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              background: 'rgba(0, 240, 255, 0.15)',
              border: '1px solid rgba(0, 240, 255, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 20px auto',
              fontSize: '24px'
            }}>
              ⚡
            </div>

            <h2 style={{
              fontSize: '22px',
              fontWeight: 700,
              marginBottom: '12px',
              background: 'linear-gradient(135deg, #FFFFFF 0%, #94A3B8 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              QUANTA UI Session Recovered
            </h2>

            <p style={{
              fontSize: '14px',
              color: '#94A3B8',
              lineHeight: 1.6,
              marginBottom: '20px'
            }}>
              A temporary rendering anomaly occurred in the live stream. The backend signal pipeline remains active and secure.
            </p>

            <div style={{ display: 'flex', gap: '12px', justify: 'center', flexWrap: 'wrap', marginBottom: '20px' }}>
              <button
                onClick={this.handleReset}
                style={{
                  background: 'linear-gradient(135deg, #00F0FF 0%, #2563EB 100%)',
                  color: '#FFFFFF',
                  border: 'none',
                  padding: '12px 24px',
                  borderRadius: '8px',
                  fontWeight: 600,
                  fontSize: '14px',
                  cursor: 'pointer',
                  boxShadow: '0 4px 14px rgba(0, 240, 255, 0.35)'
                }}
              >
                ⚡ Resume UI Session
              </button>

              <button
                onClick={this.handleReload}
                style={{
                  background: 'rgba(30, 41, 59, 0.8)',
                  color: '#94A3B8',
                  border: '1px solid rgba(148, 163, 184, 0.2)',
                  padding: '12px 20px',
                  borderRadius: '8px',
                  fontWeight: 600,
                  fontSize: '14px',
                  cursor: 'pointer'
                }}
              >
                🔄 Refresh Stream
              </button>
            </div>

            <div style={{ textAlign: 'left', marginTop: '16px' }}>
              <button
                onClick={this.toggleDetails}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#64748B',
                  fontSize: '11px',
                  cursor: 'pointer',
                  textDecoration: 'underline'
                }}
              >
                {this.state.showDetails ? 'Hide Diagnostics' : 'Show Diagnostic Trace'}
              </button>

              {this.state.showDetails && (
                <div style={{
                  marginTop: '8px',
                  padding: '12px',
                  background: '#020617',
                  border: '1px solid #1E293B',
                  borderRadius: '8px',
                  fontSize: '11px',
                  fontFamily: 'monospace',
                  color: '#EF4444',
                  overflowX: 'auto',
                  maxHeight: '160px'
                }}>
                  <div><strong>Error:</strong> {this.state.error?.toString()}</div>
                  {this.state.errorInfo?.componentStack && (
                    <div style={{ marginTop: '6px', color: '#94A3B8' }}>
                      <strong>Stack:</strong> {this.state.errorInfo.componentStack}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
