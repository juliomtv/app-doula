// Configuração da API Centralizada
const API_URL = "http://192.168.1.8:5000"; 

const API = {
    async post(endpoint, data) {
        try {
            const res = await fetch(`${API_URL}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return await res.json();
        } catch (e) {
            console.error("Erro na API:", e);
            return { status: "error", message: "Falha na conexão com o servidor." };
        }
    },
    async get(endpoint) {
        try {
            const res = await fetch(`${API_URL}${endpoint}`);
            return await res.json();
        } catch (e) {
            console.error("Erro na API:", e);
            return [];
        }
    },
    async delete(endpoint) {
        try {
            const res = await fetch(`${API_URL}${endpoint}`, { method: 'DELETE' });
            return await res.json();
        } catch (e) {
            return { status: "error" };
        }
    }
};
