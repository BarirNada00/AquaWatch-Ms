import axios from 'axios';

const API_ENDPOINTS = {
  geoserver: '/geoserver/aquawatch',
  satellite: import.meta.env.DEV ? 'http://localhost:5000' : '/satellite_processor',
};

const apiClient = axios.create({
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

apiClient.interceptors.response.use(
  response => response,
  error => {
    console.error('❌ API Error:', error.config?.url, error.message);
    return Promise.reject(error);
  }
);

export default {
  async getAnomaliesWFS() {
    console.log('📍 Calling GeoServer WFS endpoint (via proxy if dev)...');
    const wfsUrl = `${API_ENDPOINTS.geoserver}/ows`;
    console.log('WFS URL:', wfsUrl);

    try {
      const response = await apiClient.get(wfsUrl, {
        // No timeout - allow unlimited time for WFS operations as anomalies increase
        params: {
          service: 'WFS',
          version: '1.0.0',
          request: 'GetFeature',
          typeName: 'aquawatch:anomalies_gis',
          outputFormat: 'application/json'
        }
      });

      console.log('✓ WFS Response received:', response.data);
      console.log('✓ Response type:', typeof response.data);
      console.log('✓ Response keys:', Object.keys(response.data || {}));

      // If response is not GeoJSON, try to parse it
      let data = response.data;
      if (typeof data === 'string') {
        try {
          data = JSON.parse(data);
          console.log('✓ Parsed string response as JSON');
        } catch (parseError) {
          console.error('❌ Failed to parse response as JSON:', parseError);
          throw new Error('Invalid JSON response from WFS');
        }
      }

      // Validate GeoJSON structure
      if (!data || typeof data !== 'object') {
        throw new Error('WFS response is not a valid object');
      }

      if (data.type !== 'FeatureCollection') {
        console.warn('⚠ WFS response is not a FeatureCollection, wrapping it...');
        // If it's a single feature or array of features, wrap it
        if (data.type === 'Feature') {
          data = {
            type: 'FeatureCollection',
            features: [data]
          };
        } else if (Array.isArray(data)) {
          data = {
            type: 'FeatureCollection',
            features: data
          };
        } else if (data.features && Array.isArray(data.features)) {
          data.type = 'FeatureCollection';
        } else {
          throw new Error('Cannot convert WFS response to FeatureCollection');
        }
      }

      console.log('✅ Validated GeoJSON response with', data.features?.length || 0, 'features');
      return data;
    } catch (error) {
      console.error('❌ WFS Error:', error.message);
      throw new Error(`GeoServer WFS failed: ${error.message}`);
    }
  },

  async getSatelliteAOIs() {
    console.log('🛰️ Calling Satellite AOIs endpoint...');
    try {
      const response = await apiClient.get(`${API_ENDPOINTS.satellite}/aois`);
      console.log('✓ Satellite AOIs Response received:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Satellite AOIs Error:', error.message);
      throw new Error(`Satellite AOIs failed: ${error.message}`);
    }
  },

  async processSatelliteAOI(aoi) {
    console.log(`🛰️ Calling Satellite Process AOI endpoint for ${aoi}...`);
    try {
      const response = await apiClient.post(`${API_ENDPOINTS.satellite}/process/${aoi}`);
      console.log('✓ Satellite Process Response received:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Satellite Process Error:', error.message);
      throw new Error(`Satellite Process failed: ${error.message}`);
    }
  },

  async getSatelliteMetrics() {
    console.log('🛰️ Calling Satellite Metrics endpoint...');
    try {
      const response = await apiClient.get(`${API_ENDPOINTS.satellite}/metrics`, {
        timeout: 60000 // Increased timeout to 60 seconds for satellite operations
      });
      console.log('✓ Satellite Metrics Response received:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Satellite Metrics Error:', error.message);
      throw new Error(`Satellite Metrics failed: ${error.message}`);
    }
  },

  async getAnomalySummary() {
    console.log('📊 Calling Anomaly Summary endpoint...');
    try {
      const response = await apiClient.get('/api_service/summary', {
        timeout: 0  // No timeout to allow unlimited time for summary generation as anomalies increase
      });
      console.log('✓ Anomaly Summary Response received:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Anomaly Summary Error:', error.message);
      throw new Error(`Anomaly Summary failed: ${error.message}`);
    }
  }
};
