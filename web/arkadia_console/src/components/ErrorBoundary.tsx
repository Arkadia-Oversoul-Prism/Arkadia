/**
 * Surface render-failure boundary.
 *
 * A render exception anywhere inside a surface currently tears down the whole
 * tree — a blank canonical application with no recovery control. This boundary
 * catches a failed surface render and replaces only that surface with an
 * honest failure state while the shell (navigation, identity) stays usable.
 *
 * Truthfulness rules this fallback holds itself to:
 *
 *  - it states that a render failure changes nothing on the backend, and that
 *    anything shown before the failure may be incomplete — it never implies
 *    work was saved or sent;
 *  - it shows the real caught error message, not a substitute;
 *  - both recovery controls are real: a full reload, and navigation home
 *    through the shared router (the composition root keys this boundary by
 *    surface, so crossing surfaces remounts it and clears the failure state).
 *
 * The error is recorded with `console.error` — nowhere else is anything
 * reported, transmitted, or persisted.
 */
import { Component, type ErrorInfo, type ReactNode } from "react";
import { Panel } from "./ui";

interface ErrorBoundaryProps {
  /** Name of the surface being rendered — used in the honest failure copy. */
  surface: string;
  /** Real recovery action bound to the shared router by the composition root. */
  onHome: () => void;
  children: ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // The one record of the failure: the browser console. Nothing is sent.
    console.error(`[Arkadia] ${this.props.surface} failed to render`, error, info.componentStack ?? "");
  }

  render() {
    const { error } = this.state;
    if (error) {
      return (
        <div data-testid="surface-error-boundary">
          <Panel className="border-gold/30">
            <p className="font-display text-lg text-gold">{this.props.surface} could not render</p>
            <p className="mt-1 text-sm text-white/60">
              This surface failed while rendering. A render failure changes nothing on the backend,
              and anything shown before it may be incomplete — reload before trusting this screen
              again.
            </p>
            <p className="mt-3 font-mono text-xs text-white/40" data-testid="surface-error-message">
              {error.message}
            </p>
            <div className="mt-4 flex gap-2">
              <button
                type="button"
                onClick={() => window.location.reload()}
                data-testid="surface-error-reload"
                className="rounded border border-gold/40 bg-gold/10 px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest text-gold"
              >
                Reload
              </button>
              <button
                type="button"
                onClick={this.props.onHome}
                data-testid="surface-error-home"
                className="rounded border border-white/20 px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest text-white/60 hover:text-white/80"
              >
                Go to home
              </button>
            </div>
          </Panel>
        </div>
      );
    }
    return this.props.children;
  }
}
