import { Page, Panel } from "../components/ui";
import { SURFACES } from "../lib/surfaces";

export function AboutPage() {
  return (
    <Page title="About Arkadia" subtitle="One human-governed intelligence architecture, expressed through many surfaces.">
      <Panel className="mb-4">
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Product boundaries</p>
        <p className="mb-4 text-sm text-white/60">
          These are product boundaries over one canonical backend — not separate deployments.
        </p>
        <ul className="flex flex-col gap-2">
          {SURFACES.map((s) => (
            <li key={s.id} className="rounded border border-line bg-ink/40 p-3">
              <p className={`font-mono text-[11px] uppercase tracking-widest ${s.accent}`}>{s.boundary}</p>
              <p className="mt-1 text-sm text-white/80">{s.name}</p>
              <p className="text-xs text-white/45">{s.summary}</p>
            </li>
          ))}
        </ul>
      </Panel>

      <Panel>
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Principles</p>
        <ul className="flex flex-col gap-2 text-sm text-white/60">
          <li>Capability does not confer authority. Human authority remains the decision boundary.</li>
          <li>Proposal, approval, execution, and verification remain distinct.</li>
          <li>The frontend consumes real contracts and never simulates inference, authorization, execution, or verification.</li>
          <li>Personal data stays behind authentication and ownership boundaries.</li>
        </ul>
      </Panel>
    </Page>
  );
}
