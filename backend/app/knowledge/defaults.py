# when a variable hasn't been told to us or measured, we still need a starting point to reason from.
# these are conservative "degraded land" assumptions, since most users arrive because something is
# already wrong. every value seeded this way is tagged provenance='inferred', never 'user',
# so the site state panel can always be honest about what we actually know versus what we assumed.

DEFAULT_BASELINES: dict[str, float] = {
    "soil_organic_carbon": 0.5,
    "soil_ph": 6.5,
    "soil_moisture": 0.30,
    "groundwater_depth": 10.0,
    "canopy_cover": 10.0,
    "fragmentation_index": 0.55,
    "species_richness": 0.30,
    "pollinator_abundance": 0.25,
    "soil_biota_activity": 0.30,
    "nutrient_runoff": 0.40,
}
