# Sample Optical Communication Notes

Project-authored sample content for OptiLearn AI validation.

## Page 1: Fiber Attenuation

Optical fiber attenuation describes the reduction of optical power as light travels through a fiber. In introductory link budgets, attenuation is commonly represented in decibels per kilometer. If the launched power is known and the fiber attenuation coefficient is specified, learners can estimate the received power after a chosen distance.

A simple educational model treats loss as a deterministic exponential process expressed in decibel form. Increasing distance or attenuation coefficient reduces received power. This model helps learners connect a logarithmic engineering unit with a visible power trend.

Key learning checks:

- Longer fiber distance produces lower received power.
- Higher attenuation coefficient produces stronger loss.
- Decibel arithmetic is convenient for cascaded optical losses.

## Page 2: Chromatic Dispersion

Chromatic dispersion occurs because different optical wavelengths travel with different group velocities. A pulse with finite spectral width can broaden as it propagates. If broadening becomes large compared with the bit period, neighboring symbols become harder to distinguish.

An educational dispersion model uses the dispersion coefficient, source spectral width, and fiber length to estimate pulse spreading. The model supports parameter exploration rather than final system certification.

Key learning checks:

- Larger spectral width increases pulse broadening.
- Longer fiber distance increases accumulated dispersion.
- Dispersion connects optical source properties with time-domain signal quality.

## Page 3: Free-Space Optical Link Budget

A free-space optical link sends an optical beam through air rather than through a guided fiber. Received power depends on transmitted power, beam spreading, receiver aperture size, atmospheric attenuation, and pointing loss. Learners can compare how geometry and alignment affect collected power.

A simplified link budget is useful for education because each parameter has a physical interpretation. Beam divergence spreads power over a larger area. A receiver aperture captures only part of that optical field. Atmospheric attenuation and pointing error further reduce received power.

Key learning checks:

- Larger receiver aperture can collect more power.
- Larger beam divergence can reduce received irradiance at distance.
- Pointing and atmospheric losses are important engineering assumptions.

## Page 4: Modes and Rays

Guided modes describe stable field patterns that can propagate in an optical fiber. In weak-guidance education, LP modes help learners visualize intensity distributions without solving the full vector electromagnetic problem. Ray diagrams provide complementary geometric intuition.

Meridional rays pass through the fiber axis, while skew rays follow helical paths that do not necessarily cross the axis. Both views help learners reason about confinement, launch angle, and propagation path length.

Key learning checks:

- LP mode plots show spatial structure of guided fields.
- Launch coupling depends on overlap between input field and supported modes.
- Ray models are intuitive approximations, not complete wave solutions.
