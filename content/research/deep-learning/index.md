---
title: Generalizable deep learning
summary: We build deep learning models that combine climate reanalysis, satellite imagery, and in-situ records to estimate river discharge, sediment flux, and lake ice where direct measurements are sparse.
short: Deep learning
weight: 3
image_fit: contain
image_alt: Diagram of a neural network cell combining an LSTM update, a data-assimilation step, and graph message passing between river reaches.
---

River observations are uneven in space and time. A small number of sites have daily gauge records, and satellites pass over at irregular intervals. We design deep learning models that learn from several of these sources together. One example combines daily climate reanalysis with Landsat water color to produce continuous daily estimates of suspended sediment concentration, sediment flux, and discharge.

Current work extends these models to assimilate sparse observations from multiple sources, including SWOT, as they become available. The models also pass information along the river network, so estimates at one reach draw on observations upstream and downstream. We focus on models that generalize to rivers outside the training data.
