## Design notes from `Building_Design_Notes/ubermap.jpg`

### What this artifact encodes

The image is a **grid-based overland design** centered around the Tar Valon / Caemlyn / Cairhien region. It includes:

- A **legend** mapping colors to terrain/features/building intent.
- Multiple **10×10 zone grids** with zone IDs (e.g. 469/468, 509/508, 540, 539/538, 537, 569/570/568/567, 610/609/608/607, 640/639/638, etc.).
- Implied **roads**, **riverways**, **hills/mountains**, and “unbuilt”/placeholder areas.

### Legend (as shown on the left of the image)

- **Plains/farmland/grassland**: “up to builder”; more farmlands closer to cities.
- **Nothing (disconnected room)**: usually overwritten by city zones.
- **Normal zone inserted here**: usually a city or MM2 zone.
- **Towns surrounding Tar Valon**: Alindaer; others unbuilt.
- **Large hills**: vegetation up to builder.
- **Sides of Dragonmount**: very steep.
- **Mountain spire**
- **Riverway**
- **Main road**
- **Light trees / light forest**: depends on surrounding zones; if against dense forest, make a lighter forest.
- **Dense forest**

### Important note on color schemes

The legend states that **Caemlyn and Aringill use a slightly different color scheme** for terrain, but are “almost done anyway”.

### Practical implication for finishing work

This image is a strong constraint for:

- **where roads/riverways should run**
- **where terrain transitions should be abrupt vs gradual**
- **which zone grids are expected to be dense forest vs plains vs hills**
- **which parts were intentionally left “up to builder”**

