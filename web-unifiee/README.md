# Interface Web Unifiée AQUA

Interface frontend unifiée pour visualiser tous les microservices AQUA dans un tableau de bord interactif.

## Technologies

- **Vue 3** avec Composition API
- **Vite** - Build tool
- **Pinia** - State management
- **Vue Router** - Routing
- **Leaflet** - Cartographie interactive
- **Tailwind CSS** - Styling
- **Chart.js** - Graphiques (à implémenter)

## Installation

```bash
cd web-unifiee
npm install
```

## Développement

```bash
npm run dev
```

L'interface sera accessible sur `http://localhost:5173`

## Build

```bash
npm run build
```

## Structure

```
web-unifiee/
├── src/
│   ├── components/     # Composants Vue
│   ├── views/          # Pages/Vues
│   ├── stores/         # Pinia stores
│   ├── services/       # Services API
│   ├── router/         # Configuration routing
│   └── assets/         # CSS, images
```

## Fonctionnalités

- 🗺️ Carte interactive avec Leaflet
- 📊 Tableau de bord analytique
- ⚠️ Centre d'alertes
- 🛰️ Vue satellite
- 🔮 Prédictions

