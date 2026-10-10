# Data Card — California Housing

## Source
- Origin: StatLib repository, 1997 (Pace & Barry).
- Loader: `sklearn.datasets.fetch_california_housing`.
- License: Public domain / free for research use.

## Dataset Description
- 20,640 samples, 8 numeric features, 1 continuous target.
- Target: `MedHouseValue` — median house value in $100,000s.
- Features: MedInc, HouseAge, AveRooms, AveBedrms, Population,
  AveOccup, Latitude, Longitude.

## Known Limitations
- Census data from 1990; not representative of current housing markets.
- Target is capped at 5.00001 ($500,001), creating a ceiling effect.
- Spatial autocorrelation: nearby block groups are not independent.
- No categorical features in the raw dataset; preprocessing is
  numeric-only, but the pipeline structure supports categorical
  columns for future datasets.
- No timestamps; cannot evaluate temporal drift without external data.

## Preprocessing Assumptions
- Numeric features are standardised using statistics fitted **only**
  on the training split.
- Missing values: none in this dataset, but the pipeline includes a
  median imputer as a safety net for future data.
- No target transformation is applied in the baseline.