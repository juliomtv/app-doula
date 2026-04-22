// Configuração da API Centralizada
const API_URL = "SUA_URL_DA_API_AQUI"; // Ex: https://sua-api.herokuapp.com

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

// --- MODIFICAÇÕES PARA O APP CLIENTE ---
// Substituir a função doLogin() original:
/*
async function doLogin() {
    const email = document.getElementById('l-user').value.trim();
    const pass = document.getElementById('l-pass').value;
    const err = document.getElementById('l-err');
    
    if(!email || !pass) { err.textContent = 'Preencha os campos.'; return; }
    
    const res = await API.post('/api/login', { email, senha: pass });
    if(res.status === "success") {
        currentUser = res.user;
        DB.set('nn_session', currentUser.id);
        goApp();
    } else {
        err.textContent = res.message;
    }
}
*/

// --- MODIFICAÇÕES PARA O APP ADMIN ---
// Substituir a função adminLogin() original:
/*
async function adminLogin() {
    const user = document.getElementById('a-user').value.trim();
    const pass = document.getElementById('a-pass').value;
    const err = document.getElementById('a-err');
    
    const res = await API.post('/api/admin/login', { user, pass });
    if(res.status === "success") {
        DB.set('nn_admin_session', res.token);
        document.getElementById('admin-login').style.display='none';
        document.getElementById('admin-shell').classList.add('active');
        renderDashboard();
    } else {
        err.textContent = res.message;
    }
}
*/
