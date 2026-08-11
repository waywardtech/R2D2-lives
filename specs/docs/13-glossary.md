# 13 - Glossary

| Term | Meaning in this project |
|---|---|
| Agent / Mobile Agent | A physical or simulated platform that can report state and optionally move/emit probes through SAP. R2 is the first physical agent. |
| Advisory | Time-bounded, evidence-backed spatial information that an agent may accept, modify, or reject; never a motor command. |
| Artifact | Immutable binary/structured evidence or output referenced by identity, media type, and SHA-256 hash. |
| Bat-Space Modeler / BSM | Standalone active-acoustic localization and mapping product. |
| BLE owner | The single R2 process/module allowed to hold the droid Bluetooth connection and serialize commands. |
| Capability | Publicly advertised behavior or evidence type with a verification state and limits. |
| Clock domain | A device/source monotonic time basis with identity, offset/drift, synchronization method, and uncertainty. |
| Continuity | Persistent linkage of dialogue, entities, claims, actions, events, poses, map features, and provenance. |
| Discovery | Stock-app-like supervised wander/pause/look/react/learn behavior; distinct from route-following Patrol and BSM mapping. |
| Event receipt time | When a consumer received data; not necessarily when the physical measurement happened. |
| Frame | Named coordinate system such as world, map revision, agent odometry, body, probe source, or microphone channel. |
| Hardware-in-loop / HIL | A test using real Pi/R2/audio hardware; separately authorized and disabled by default. |
| Lease | Short-lived local authorization defining who may request bounded motion and when the BLE owner must stop. |
| Map revision | Immutable BSM world-model snapshot with parent/evidence/calibration/algorithm/artifact metadata. |
| Mapping Mission | Coordinated safe poses/holds/probe emissions/captures intended to produce spatial evidence. |
| Observation | Timestamped, provenance-bearing evidence such as pose, collision, recording metadata, or tag context. |
| Patrol | Execution of a previously approved, versioned route. |
| Probe | Known acoustic waveform plus characterized source, emission timing/gain, and mounting transform. |
| R2 Agent Runtime | Raspberry Pi product that owns R2 BLE, safety, behavior, voice, continuity, PWA, and SAP Agent API. |
| Safe hold | Canonical stopped, non-resuming safety state entered by stop, faults, lease expiry, or uncertainty. |
| SAP | Spatial Agent Protocol: versioned public contract between Mobile Agents and Spatial Providers. |
| Spatial Provider | A system that estimates location/geometry and issues advisories through SAP. BSM is the first provider. |
| Speaker Attention | Coarse "look toward the active speaker zone/bearing" function; not BSM mapping or speaker identity. |
| Talk-to-Tag | Grounding natural-language descriptions and deictic phrases in recent events/poses/entities/map evidence. |
| Unknown space | Region without adequate evidence; explicitly not equivalent to free/navigable space. |

