# Web Dashboard (Liquid Glass)

The Web Dashboard is an interactive, real-time React application used to monitor and control the evolutionary algorithm engine remotely.

## Architecture & Technology

The dashboard resides in the `dashboard/` directory and is built using modern web development standards:
- **React**: For declarative, component-driven UI.
- **Vite**: As a fast development server and build tool.
- **Native WebSockets**: For real-time telemetry streaming from the Python engine.
- **Lucide React**: For scalable, premium vector icons.

## Design Aesthetic: Liquid Glass

The UI implements a premium "Liquid Glass" (glassmorphism) design system to provide an immersive user experience:
- **Floating Orbs**: Abstract, glowing spheres in the background visually encode the engine's state (Green/Blue for running, Amber for paused, Crimson for offline/stopped).
- **Glass Panels**: Frosted, translucent panels (`backdrop-filter: blur()`) house the telemetry and controls.
- **Dynamic Feedback**: Operations smoothly slide into the feed, and error/offline states trigger floating toast notifications.

## Connecting to the Engine

The React application connects automatically to `ws://localhost:8765`. 
If the Python engine is not running, the dashboard transitions into a graceful "Engine Offline" state, preventing the user from sending dead commands.

## Running the Dashboard

To launch the dashboard locally for development:
```bash
cd dashboard
npm install
npm run dev
```
