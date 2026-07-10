# 002. React + TypeScript Frontend

## Status
ACCEPTED (supersedes the "Vanilla JS, no framework" decision in [001](001-tech-stack.md))

## Context
ADR-001 chose Vanilla JS to avoid build complexity. As the UI grew
(stats panel with multiple charts, i18n, theming, area selection state shared
between sidebar / map / panel), hand-rolled DOM state management became the
main source of bugs.

## Decision
The frontend is a **React 18 + TypeScript + Vite** SPA:

- **React** — shared state (active layer, selected area, date, draw mode)
  lives in `App` and flows down through props; no state library needed at
  this scale.
- **TypeScript** — API response types (`AreaStatistics`, `AreaChange`, …)
  are checked at build time.
- **Vite** — fast HMR in dev (used inside Docker via the dev compose),
  manual chunk splitting for maplibre / chart.js in prod.
- MapLibre GL JS stays (unchanged from ADR-001).

## Consequences
- A build step exists; the production Docker image builds the bundle and
  serves it via nginx.
- i18n and theming are implemented as small hooks
  (`useTranslation` with a module-level store) rather than heavy libraries.
