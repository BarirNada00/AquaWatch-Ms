import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import AnalyticsView from '../views/AnalyticsView.vue';
import AlertsView from '../views/AlertsView.vue';
import SatelliteView from '../views/SatelliteView.vue';
import PredictionsView from '../views/PredictionsView.vue';

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/analytics',
    name: 'analytics',
    component: AnalyticsView
  },
  {
    path: '/alerts',
    name: 'alerts',
    component: AlertsView
  },
  {
    path: '/satellite',
    name: 'satellite',
    component: SatelliteView
  },
  {
    path: '/predictions',
    name: 'predictions',
    component: PredictionsView
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;

