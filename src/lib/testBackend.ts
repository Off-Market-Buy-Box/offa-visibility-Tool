// Simple test to check if backend is accessible
export async function testBackendConnection(): Promise<boolean> {
  try {
    const response = await fetch('http://127.0.0.1:8000/health');
    return response.ok;
  } catch (error) {
    console.error('Backend connection test failed:', error);
    return false;
  }
}

// Test API endpoints
export async function testEndpoints() {
  const endpoints = [
    '/api/v1/keywords/',
    '/api/v1/competitors/',
    '/api/v1/smart-tasks/',
    '/api/v1/reddit/mentions'
  ];

  const results: Record<string, boolean> = {};

  for (const endpoint of endpoints) {
    try {
      const response = await fetch(`http://127.0.0.1:8000${endpoint}`);
      results[endpoint] = response.ok;
      console.log(`${endpoint}: ${response.ok ? '✅' : '❌'} (${response.status})`);
    } catch (error) {
      results[endpoint] = false;
      console.error(`${endpoint}: ❌ Error:`, error);
    }
  }

  return results;
}
