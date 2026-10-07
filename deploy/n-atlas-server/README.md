# N-ATLaS ephemeral validation gateway

This service exposes N-ATLaS behind an OpenAI-compatible `/v1/chat/completions` API for PS1 validation.

It uses a public GGUF quantization derived from NCAIR1/N-ATLaS. It is validation infrastructure, not a substitute for the official hosted N-ATLAS endpoint.

Required:
- N_ATLAS_MODEL_FILE
- optional N_ATLAS_API_KEY

The service loads the model lazily on the first inference request.