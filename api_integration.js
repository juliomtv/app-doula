// Configuração da API Centralizada (Dinâmica)
let API_URL = localStorage.getItem('api_url') || 'http://localhost:5000';

function setApiUrl(url) {
  API_URL = url;
  localStorage.setItem('api_url', url);
  console.log('API URL atualizada para:', API_URL);
} 

const API = {
    async post(endpoint, data) {
        try {
            let baseUrl = API_URL;
            if (!baseUrl.startsWith('http')) baseUrl = 'http://' + baseUrl;
            const url = `${baseUrl.replace(/\/$/, '')}/${endpoint.replace(/^\//, '')}`;
            
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (e) {
            console.error("Erro na API:", e);
            return { status: "error", message: "Falha na conexão com o servidor. Verifique a URL da API." };
        }
    },
    async get(endpoint) {
        try {
            let baseUrl = API_URL;
            if (!baseUrl.startsWith('http')) baseUrl = 'http://' + baseUrl;
            const url = `${baseUrl.replace(/\/$/, '')}/${endpoint.replace(/^\//, '')}`;
            
            const res = await fetch(url);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (e) {
            console.error("Erro na API:", e);
            return [];
        }
    },
    async delete(endpoint) {
        try {
            let baseUrl = API_URL;
            if (!baseUrl.startsWith('http')) baseUrl = 'http://' + baseUrl;
            const url = `${baseUrl.replace(/\/$/, '')}/${endpoint.replace(/^\//, '')}`;
            
            const res = await fetch(url, { method: 'DELETE' });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (e) {
            console.error("Erro na API:", e);
            return { status: "error" };
        }
    }
};
