import { Component } from 'react';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    // In production this is where an error-reporting service would be called.
    console.error('BugFix AI crashed:', error, info);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <div
        role="alert"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          gap: '12px',
          padding: '24px',
          textAlign: 'center',
          background: '#0d0d1a',
          color: '#e8e8f0',
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        }}
      >
        <div style={{ fontSize: '40px' }}>🐞💥</div>
        <h1 style={{ fontSize: '20px', margin: 0 }}>Something went wrong</h1>
        <p style={{ color: '#a0a0c0', maxWidth: '420px', margin: 0 }}>
          BugFix AI hit an unexpected error. Your chat history is safe in local storage.
        </p>
        <button
          onClick={this.handleReset}
          style={{
            marginTop: '8px',
            background: '#2563eb',
            color: 'white',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: 500,
          }}
        >
          Try again
        </button>
      </div>
    );
  }
}

export default ErrorBoundary;
