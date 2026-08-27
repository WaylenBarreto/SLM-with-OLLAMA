# Quality, Speed, and Resource Tradeoffs

This document records observations from real benchmark runs. It intentionally contains no example scores: results belong in generated reports after measurements are collected on a specific machine.

## Working hypothesis

Smaller models should generally load faster, consume less RAM, and produce higher token throughput. Larger models may improve reasoning, coding, and instruction-following quality, but can increase cold-start latency and memory pressure. The benchmark exists to test this hypothesis rather than assume it.

## Interpretation rules

- Compare models only when they received the same dataset version, settings, repetition count, and hardware snapshot.
- Separate cold-start latency from warm-run latency where possible.
- Treat tokens per second and time to first token as different signals: a model can begin slowly but generate quickly afterward.
- Do not rank a model on quality alone; include latency and resource constraints relevant to the intended workload.
- GPU and VRAM values must remain unavailable when the host cannot provide reliable dynamic telemetry.

## Limitations

CPU scheduling, background applications, thermal throttling, model caching, and Ollama load state can change measurements. Repeated runs reduce noise but do not eliminate it. Deterministic checks cover structured and objective tasks well; open-ended quality remains only partially captured without a separately documented judge.
