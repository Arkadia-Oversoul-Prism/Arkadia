FROM ghcr.io/ggml-org/llama.cpp:server

# The upstream image declares ENTRYPOINT ["/app/llama-server"] (exec form). A shell-form CMD
# is appended to an exec-form ENTRYPOINT as extra argv, so the pair below previously produced
# "/app/llama-server /bin/sh -c '/app/llama-server -hf ...'" and llama-server exited with
# "error: invalid argument: /bin/sh" - the image could not start at all. Verified by building
# and running this image on 2026-10-10; see
# docs/control-plane/evidence/runtime-acceptance-6115de9a-aeas04/NATLAS-SELFHOST-CUTOVER-01.md.
#
# Clearing the inherited ENTRYPOINT makes the shell-form CMD the whole command, so ${PORT} and
# ${N_ATLAS_MODEL_REPO} keep expanding as intended and the server is PID 1.
ENTRYPOINT []

ENV N_ATLAS_MODEL_REPO=QuantFactory/N-ATLaS-GGUF:Q4_K_M

CMD /app/llama-server -hf ${N_ATLAS_MODEL_REPO} --host 0.0.0.0 --port ${PORT} -c 4096 -n 256