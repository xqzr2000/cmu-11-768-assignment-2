# Proposed architecture: offline-first evaluation with Docker

```text
               OFFLINE (Phase 0 / Phase 1)
  upstream seed result.json + figure.png + input files
                        |
                        v
     Dataset/schema preflight -> human label inventory
                        |
                        v
          independent validator predictions
                        |
                        v
       official workflow score / per-family MCC

                ONLINE (later phases)
        task.json and task-local inputs
                        |
                        v
       mini-SWE-agent controller (host)
              |                    |
   OpenAI-compatible API      bounded bash tools
   Z.ai GLM-4.7-Flash          Docker Sandbox
   (retry on 429/1305)         (no API secrets)
              |                    |
              +------ agent trajectory ------+
                              |
                     figure.png + result.json
                              |
                       VLM validator
                (model / endpoint TBD)
                              |
               predictions + human review
                              |
                      scoring and Harbor
```

## Separation of concerns

- **Controller:** holds model API credentials, orchestrates agent steps, records trajectories, enforces attempt budget.
- **Task sandbox:** uses the pinned `agent-sandbox-runtime` package; runs untrusted model-proposed commands without credentials or Docker socket.
- **Provider adapter:** uses a remote OpenAI-compatible endpoint, with bounded retries for transient failures; it never equates transport errors with an agent's task failure.
- **Validator:** examines task, trajectory, inputs, and final figure. Its own mistakes are analyzed independently of visualization-agent mistakes.
- **Scorer:** preserves official MCC semantics, including exclusion of terminal execution failures from the other three category denominators.
- **Harbor:** runs deterministic checks with oracle and intentionally incorrect mutant solutions, documenting what those tests miss.

## Research validity safeguards

1. Never hard-code public run IDs or labels into the validator.
2. Preserve original seed artifacts unchanged. Save generated outputs separately.
3. Distinguish a valid image from a correct and readable chart.
4. Use held-out grouping when estimating generalization; public labels are not private grading labels.
5. Record model IDs, endpoints, parameters, attempts, timeout limits, provenance, and per-run artifacts.
6. Disclose deviations from the official checkpoint or agent scaffold.
7. Do not treat successful basic API tool calling as evidence of a working multi-step agent.

## Sandbox details still to implement

The Assignment 1 package exposes Docker lifecycle and shell-command execution. Our adaptation still needs explicit task-input staging, a read-back path for `figure.png`, a locally compatible mini-SWE-agent execution environment, and side-by-side trajectory comparisons. No such end-to-end claims are made in Phase 0.
