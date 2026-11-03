import './App.css'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { useAuth } from './authContext';
import { useEffect, useState } from 'react';
import { Home } from './Home';
import { Login } from './Login';
import { SignUp } from './SignUp';
import { AgdBancada } from './AgdBancada';
import { Bancada } from './Bancada';
import { Estoque } from './Estoque';
import { AdcEstoque } from './AdcEstoque';
import { Carrinho } from './Carrinho';
import { EmailVerification } from './EmailVerification';
import { AuthProvider } from './AuthContext';
import { Restaurant } from './Restaurant';
import { Dish } from './Dish';
import { Order } from './Order';
import { Profile } from './Profile';
import { Stock } from './Manager/Stock';
import { StockAdd } from './Manager/StockAdd';
import { Dashboard } from './Manager/Dashboard';

/*Mudar isso depois pra ver como ficará melhor*/
function ProtectedRoute({ children, allowedRoles }) {
  const { user, sessionStatus } = useAuth();
  const location = useLocation();
  if (sessionStatus === 'loading') return <main aria-live="polite">Verificando sessão…</main>;
  if (!user) return <Navigate to="/login" replace state={{ from: `${location.pathname}${location.search}` }} />;
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <main role="status"><h1>Acesso restrito</h1><p>Seu perfil não tem permissão para acessar esta página.</p></main>;
  }
  return children;
}

function PreferencesAndAccessibility() {
  const [preference, setPreference] = useState(() => localStorage.getItem('theme-preference') || 'system');
  useEffect(() => {
    document.documentElement.dataset.theme = preference;
    document.documentElement.style.colorScheme = preference === 'system' ? '' : preference;
    localStorage.setItem('theme-preference', preference);
  }, [preference]);
  useEffect(() => {
    if (document.getElementById('vlibras-plugin')) return;
    const script = document.createElement('script');
    script.id = 'vlibras-plugin';
    script.src = 'https://vlibras.gov.br/app/vlibras-plugin.js';
    script.async = true;
    script.onerror = () => script.remove();
    document.body.appendChild(script);
  }, []);
  return <label className="theme-control">Tema
    <select aria-label="Preferência de tema" value={preference} onChange={(event) => setPreference(event.target.value)}>
      <option value="system">Seguir sistema</option><option value="light">Claro</option><option value="dark">Escuro</option>
    </select>
  </label>;
}

function Protected({ children, roles }) { return <ProtectedRoute allowedRoles={roles}>{children}</ProtectedRoute>; }


function App() {
return (
    <AuthProvider>
    <PreferencesAndAccessibility />
    <Routes>
      <Route path='/' element={<Home/>}/>
      <Route path='/login' element={<Login/>}/>
      <Route path='/cadastro' element={<SignUp/>}/>
      <Route path='/cadastro/autenticar' element={<EmailVerification/>}/>
      <Route path='/AgdBancada' element={<Protected><AgdBancada/></Protected>}/>
      <Route path='/Bancada' element={<Protected><Bancada/></Protected>}/>
      <Route path='/Estoque' element={<Protected roles={['admin']}><Estoque/></Protected>}/>
      <Route path='/AdcEstoque' element={<Protected roles={['admin']}><AdcEstoque/></Protected>}/>
      <Route path='/Carrinho' element={<Protected><Carrinho/></Protected>}/>
      <Route path='/recuperar-senha' element={<PasswordRecovery/>}/>
      <Route path='/redefinir-senha' element={<PasswordReset/>}/>
      <Route path='/restaurante/:id' element={<Restaurant/>}/>
      <Route path='/prato/:id' element={<Dish/>}/>
      <Route path='/pedido' element={<Order/>}/>
      <Route path='/perfil' element={<Profile/>}/>
      <Route path='/gerente/estoque' element={<Stock/>}/>
      <Route path='/gerente/estoque/adicionar' element={<StockAdd/>}/>
      <Route path='/gerente/dashboard' element={<Dashboard/>}/>
    </Routes>
    </AuthProvider>
  )

}

/*Isso aq mudar tbm, tá aq pq n sei onde deixar :)*/
function PasswordRecovery() {
  const [message, setMessage] = useState('');
  async function submit(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      const csrf = await (await fetch('/api/csrf-token', { credentials: 'include' })).json();
      const response = await fetch('/api/password-reset/request', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrf_token }, body: JSON.stringify({ email: form.get('email') }) });
      const result = await response.json();
      setMessage(result.message || result.error?.message || 'Não foi possível solicitar a redefinição.');
    } catch { setMessage('Não foi possível conectar ao servidor.'); }
  }
  return <main className="auth-flow"><h1>Recuperar senha</h1><form onSubmit={submit}><label>Email <input name="email" type="email" required autoComplete="email" /></label><button type="submit">Enviar instruções</button></form><p role="status">{message}</p></main>;
}

function PasswordReset() {
  const [message, setMessage] = useState('');
  async function submit(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      const token = new URLSearchParams(window.location.search).get('token');
      if (!token) {
        setMessage('Link inválido ou sem token de redefinição.');
        return;
      }
      const csrf = await (await fetch('/api/csrf-token', { credentials: 'include' })).json();
      const response = await fetch('/api/password-reset/confirm', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrf.csrf_token
        },
        body: JSON.stringify({
          token: token,
          password: form.get('password'),
          password_confirmation: form.get('password_confirmation')
        })
      });
      const result = await response.json();
      setMessage(result.message || result.error?.message || 'Não foi possível redefinir a senha.');
    } catch (error) {
      console.error('Erro ao redefinir senha:', error);
      setMessage('Não foi possível conectar ao servidor.');
    }
  }
  return <main className="auth-flow"><h1>Definir nova senha</h1><form onSubmit={submit}><label>Nova senha <input name="password" type="password" required autoComplete="new-password" /></label><label>Confirme a senha <input name="password_confirmation" type="password" required autoComplete="new-password" /></label><button type="submit">Salvar senha</button></form><p role="status">{message}</p></main>;
}


export default App
