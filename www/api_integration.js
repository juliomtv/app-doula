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
            const res = await fetch(`${API_URL}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (e) {
            console.error("Erro na API:", e);
            console.error("URL tentada:", `${API_URL}${endpoint}`);
            return { status: "error", message: "Falha na conexao com o servidor." };
        }
    },
    async get(endpoint) {
        try {
            const res = await fetch(`${API_URL}${endpoint}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (e) {
            console.error("Erro na API:", e);
            console.error("URL tentada:", `${API_URL}${endpoint}`);
            return [];
        }
    },
    async delete(endpoint) {
        try {
            const res = await fetch(`${API_URL}${endpoint}`, { method: 'DELETE' });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (e) {
            console.error("Erro na API:", e);
            console.error("URL tentada:", `${API_URL}${endpoint}`);
            return { status: "error" };
        }
    }
};
