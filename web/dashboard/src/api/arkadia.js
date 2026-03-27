const BASE_URL = "https://arkadia-n26k.onrender.com";

export async function fetchHeartbeat() {
  const res = await fetch(`${BASE_URL}/api/heartbeat`);
  if (!res.ok) throw new Error(`Heartbeat failed: ${res.status}`);
  return res.json();
}

export async function fetchCorpus() {
  const res = await fetch(`${BASE_URL}/api/corpus`);
  if (!res.ok) throw new Error(`Corpus fetch failed: ${res.status}`);
  return res.json();
}

export async function postOracleQuery(message) {
  const res = await fetch(`${BASE_URL}/api/commune/resonance`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, priority: "high" }),
  });
  if (!res.ok) throw new Error(`Oracle query failed: ${res.status}`);
  return res.json();
}
