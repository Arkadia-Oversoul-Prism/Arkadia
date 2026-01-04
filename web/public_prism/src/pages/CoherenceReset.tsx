import { useState } from "react";

type Tier = "free" | "mid" | "premium";

interface CoherenceResetProps {
  userTier?: Tier;
}

export default function CoherenceReset({ userTier = "free" }: CoherenceResetProps) {
  const [emotionalState, setEmotionalState] = useState("");
  const [pressurePoint, setPressurePoint] = useState("");
  const [output, setOutput] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleReset = async () => {
    setLoading(true);
    setOutput(null);

    try {
      const response = await fetch("/api/coherence-reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ emotionalState, pressurePoint, tier: userTier }),
      });
      const data = await response.json();
      setOutput(data.result);
    } catch (err) {
      setOutput("Error connecting to server.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto p-8 bg-white/5 backdrop-blur-lg rounded-2xl border border-white/10 text-white mt-12">
      <h2 className="text-3xl font-bold mb-6 text-[#D4AF37]">Coherence Reset</h2>

      <div className="space-y-4">
        <div>
          <label className="block mb-2 text-sm uppercase tracking-widest opacity-70">Current Emotional State</label>
          <input
            type="text"
            value={emotionalState}
            onChange={(e) => setEmotionalState(e.target.value)}
            className="w-full p-3 bg-black/20 border border-white/10 rounded-lg focus:outline-none focus:border-[#D4AF37] transition-colors"
            placeholder="e.g., stressed, anxious"
          />
        </div>

        <div>
          <label className="block mb-2 text-sm uppercase tracking-widest opacity-70">Pressure Point (optional)</label>
          <input
            type="text"
            value={pressurePoint}
            onChange={(e) => setPressurePoint(e.target.value)}
            className="w-full p-3 bg-black/20 border border-white/10 rounded-lg focus:outline-none focus:border-[#D4AF37] transition-colors"
            placeholder="e.g., deadline, meeting"
          />
        </div>

        <button
          onClick={handleReset}
          disabled={loading}
          className="w-full bg-[#D4AF37] text-[#001F3F] font-bold p-4 rounded-lg hover:bg-[#7FDBFF] transition-all transform active:scale-95 disabled:opacity-50"
        >
          {loading ? "Aligning..." : "Initialize Reset"}
        </button>
      </div>

      {output && (
        <div className="mt-8 p-6 border border-[#D4AF37]/30 bg-[#D4AF37]/10 rounded-xl animate-in fade-in slide-in-from-bottom-4">
          <strong className="block text-[#D4AF37] mb-2 uppercase text-xs tracking-widest">Oracle Guidance:</strong>
          <p className="text-lg italic leading-relaxed text-[#7FDBFF]">{output}</p>
        </div>
      )}

      {userTier === "free" && (
        <p className="mt-6 text-center text-xs text-white/40 uppercase tracking-widest">
          Free tier: Basic 2-minute reset protocol active.
        </p>
      )}
    </div>
  );
}
