curl https://arkana-rasa.onrender.com/status

curl -X POST https://arkana-rasa.onrender.com/oracle \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "zahrune",
    "message": "Arkana, speak from Codex-State: name A01, A02, A03, A07 as you know them, and describe how they form your Codex Spine."
  }'
