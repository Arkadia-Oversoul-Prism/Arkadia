FROM ghcr.io/ggml-org/llama.cpp:server

ENV N_ATLAS_MODEL_REPO=QuantFactory/N-ATLaS-GGUF:Q4_K_M

CMD /app/llama-server -hf ${N_ATLAS_MODEL_REPO} --host 0.0.0.0 --port ${PORT} -c 4096 -n 256