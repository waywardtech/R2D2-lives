# R2 Runtime scaffold

Phase 0 supplies simulation-only adapters. `SimDroidDriver` records safe-hold
state and never addresses BLE. `NullSpatialProviderClient` and
`SimSpatialProviderClient` are chosen by the `R2_SPATIAL_PROVIDER` configuration
value. Real hardware support is deliberately absent until Phase 1 and must be
separately armed and supervised.

