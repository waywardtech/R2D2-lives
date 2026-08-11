# 00 - Product charter

## Product vision

Create an R2-D2 interface that feels alive, attentive, useful, and continuous while remaining a safe, deterministic physical robot system. In parallel, create a reusable acoustic spatial intelligence that can treat R2 as its first mobile probe without becoming an R2 accessory.

The user experience is character-driven; the engineering foundation is contract-driven.

## Product A: R2 Agent Runtime

R2 Agent Runtime turns a Sphero R2-D2 R201 and Raspberry Pi into an always-available local service that can:

- accept manual, voice, web, and integration requests;
- translate meaning into R2 sounds, LEDs, head/leg movement, and safe locomotion;
- reproduce a stock-app-like **Discovery / Explore and Learn** experience;
- attach ordinary spoken language to locations and encounters through **Talk-to-Tag**;
- maintain dialogue, entity, event, and spatial continuity;
- report battery, connection, Pi health, collision, and suspected stuck conditions;
- expose a generic mobile-agent interface to a spatial provider;
- consume spatial localization, hazard, and route advisories from any conforming provider;
- optionally monitor read-only information sources such as email and headlines without treating their contents as commands.

## Product B: Bat-Space Modeler

Bat-Space Modeler is an independent acoustic mapping and localization product that can:

- coordinate fixed microphone nodes and one or more mobile or stationary probe sources;
- ingest calibrated recordings and agent pose/telemetry observations;
- estimate direct paths, reflections, source positions, surfaces, openings, obstacles, and uncertainty;
- build an immutable, revisioned 3D world model from a blank geometric prior or an optional blueprint prior;
- issue generic localization and route/hazard advisories;
- simulate rooms, arrays, clocks, noise, probe agents, and mapping missions;
- work with R2 first, then other agents without product-code changes.

"Blank slate" means no assumed blueprint or semantic room knowledge. It does not remove the mathematical need to establish a coordinate origin, scale, time basis, and calibration evidence.

## Canonical operating modes

| Mode | Purpose | Route knowledge | Mapping behavior |
|---|---|---:|---|
| Manual | Human directly requests bounded movement or expression | Optional | None unless observations are explicitly recorded |
| Discovery | Wander, pause, look, react, converse, and learn tags in a stock-app-like style | Not required | Produces encounters and semantic tags; does not claim geometric reconstruction |
| Patrol | Follow a previously validated route or waypoint sequence | Required | Detects deviations and records observations |
| Mapping Mission | Execute measurement poses, headings, holds, and probe emissions requested through SAP | Mission-specific | Produces synchronized evidence for BSM |
| Attention | Turn head/body toward the likely active speaker zone | Coarse speaker zone | No navigation; no acoustic room reconstruction |
| Charging Staging | Navigate to a safe waiting point and request human cable connection | Required | No self-plugging claim |
| Safe Hold | Stop locomotion and maintain a safe, observable state | None | Entered on faults, lease expiry, or explicit stop |

Speaker Attention and Bat-Space mapping are intentionally separate. The first multi-microphone feature answers only "which direction should R2 look?" BSM consumes independently calibrated, timestamped evidence for spatial modeling.

## Primary users

- **Owner/operator:** speaks to R2, supervises movement, names things, reviews notifications, and authorizes hardware tests.
- **Developer:** builds adapters, behavior, simulation, APIs, and spatial algorithms.
- **System operator:** deploys and monitors Pi and BSM services, credentials, storage, and backups.
- **Integration developer:** connects another spatial provider or another mobile probe agent through SAP.

## Product principles

1. **Character above chatter:** R2 communicates through a consistent expressive language, not random clips.
2. **Safety above autonomy:** deterministic control always outranks conversational intent.
3. **Advisory spatial intelligence:** a spatial provider informs movement; the agent retains actuation authority.
4. **Continuity with provenance:** remembered facts remain linked to who/what/where/when and confidence.
5. **Replaceability from day one:** all unstable libraries and external services sit behind owned adapters.
6. **Evidence before claims:** simulation, calibration, and real-room validation are separate gates.
7. **Local-first privacy:** microphones, messages, and maps stay local unless the operator explicitly configures otherwise.
8. **Graceful degradation:** loss of internet, LLM, BSM, microphone nodes, or email must not prevent local stop, status, or safe manual control.

## MVP definition

The R2 MVP is complete before significant BSM algorithm development begins. It includes:

- persistent BLE ownership, reconnect, and capability probe;
- bounded manual control and emergency stop;
- R2 expressions and deterministic expression compiler;
- telemetry, health, collision/stuck inference, and event persistence;
- simulated driver and record/replay;
- basic wake/voice command path with offline critical commands;
- Discovery and Talk-to-Tag at a supervised, conservative movement envelope;
- generic SAP Agent endpoint and generic Spatial Provider client exercised against simulators;
- Safari PWA for control, status, tags, and diagnostics;
- install, service, backup, and recovery procedures on Raspberry Pi.

The R2 MVP does **not** require a working acoustic 3D map. Integration blockers are prevented through the protocol, adapter, time/frame, uncertainty, and event requirements implemented against fakes.

## BSM MVP definition

BSM MVP begins after the R2 MVP gate and includes:

- generic agent simulator and SAP client;
- deterministic acoustic simulation with ground truth;
- microphone-node enrollment, calibration, and clock-quality reporting;
- known-probe detection and room impulse response extraction;
- initial source localization and one or more surface hypotheses with uncertainty;
- immutable map revisions and visual inspection artifacts;
- mapping-mission coordination against SimAgent, then R2 through the same client;
- safe route/hazard advisories consumed by R2 as non-authoritative information.

## Explicit non-goals for the first releases

- Unsupervised public-area operation
- Guaranteed collision avoidance based only on consumer-device microphones
- Physical self-connection of the stock R201 USB charger
- Direct motor control by an LLM or BSM
- Treating stock R2 sounds as calibrated broadband probes without measurement
- Precise multi-device timing from browser arrival timestamps
- Identifying people from voice or recording continuous room audio by default
- Autonomous interception, pursuit, or orbit of people or animals
- A claim that the reconstructed map is survey-grade

## Success measures

- R2 remains safely controllable and useful when all optional AI/cloud services are unavailable.
- BSM can substitute SimAgent for R2 without changing mapping logic.
- R2 can substitute NullSpatialProvider or SimSpatialProvider for BSM without changing behavior logic.
- A recorded integration session can be replayed deterministically and produces traceable map/advisory outcomes.
- Spoken tags such as "edge of the carpet" resolve to the original event, pose evidence, and later map feature when available.
- Every product release states measured error, uncertainty, supported operating envelope, and known limitations.

