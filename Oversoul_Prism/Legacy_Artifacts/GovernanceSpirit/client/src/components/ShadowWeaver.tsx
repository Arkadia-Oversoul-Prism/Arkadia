import { ErrorBoundary } from "react-error-boundary";
import { ReactNode } from "react";
import { useGate } from "../lib/GateContext";

type ShadowWeaverProps = {
  children: ReactNode;
};

export default function ShadowWeaver({ children }: ShadowWeaverProps) {
  const { reset: resetGate } = useGate();

  const Fallback = ({
    error,
    resetErrorBoundary,
  }: {
    error: Error;
    resetErrorBoundary: () => void;
  }) => (
    <div className="relative h-screen w-screen bg-[url('/svg/cosmic-web.svg')] bg-cover p-8">
      <div className="mx-auto flex max-w-2xl flex-col items-center justify-center gap-6 rounded-xl bg-cosmic-slate/90 p-8 backdrop-blur-lg">
        <div className="flame-glyph text-6xl">𓁶</div>
        <h2 className="font-mystic text-2xl text-cosmic-gold">
          Shadow Fragment Detected
        </h2>
        <div className="text-cosmic-light rounded-lg bg-cosmic-black/80 p-4 font-mono text-sm">
          {error.message}
        </div>
        <p className="text-center text-cosmic-lavender">
          The Spiral encounters resistance. Purify this shadow?
        </p>
        <div className="flex gap-4">
          <button
            onClick={() => {
              resetErrorBoundary();
              resetGate();
            }}
            className="portal-button rounded-lg bg-cosmic-gold px-6 py-2 text-cosmic-black hover:bg-cosmic-gold/90"
          >
            Purify Sigil
          </button>
          <button
            onClick={() => window.location.reload()}
            className="portal-button rounded-lg border border-cosmic-gold px-6 py-2 text-cosmic-gold hover:border-cosmic-gold/70 hover:text-cosmic-gold/80"
          >
            Rekindle Flame
          </button>
        </div>
      </div>
      <div className="absolute inset-0 flame-watermark opacity-10" />
    </div>
  );

  return (
    <ErrorBoundary
      FallbackComponent={Fallback}
      onReset={() => {
        // Reset app state here if needed
      }}
    >
      {children}
    </ErrorBoundary>
  );
}