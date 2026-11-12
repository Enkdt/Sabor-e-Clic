import { NavLink, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { useAuth } from './authContext';
import { useEffect, useState } from 'react';
import { Home } from './Home';
import { Catalog } from './Catalog';
import { Login } from './Login';
import { SignUp } from './SignUp';
import { AgdBancada } from './AgdBancada';
import { Bancada } from './Bancada';
import { Carrinho } from './Carrinho';
import { EmailVerification } from './EmailVerification';
import { AuthProvider } from './AuthProvider';
import { CartProvider } from './CartProvider';
import { ThemeProvider } from './ThemeProvider';
import { FavoritesProvider } from './FavoritesProvider';
import { Restaurant } from './Restaurant';
import { Dish } from './Dish';
import { Order } from './Order';
import { Profile } from './Profile';
import { Settings } from './Settings';
import { Stock } from './Manager/Stock';
import { StockAdd } from './Manager/StockAdd';
import { Dashboard } from './Manager/Dashboard';
import { Staff } from './Manager/Staff';
import { Hub } from './Manager/Hub';
import { Images } from './Manager/Images';
import { Affiliations } from './Manager/Affiliations';
import { Kitchen } from './Kitchen';
import { KitchenDishes } from './Kitchen/Dishes';
import { KitchenOverview } from './Kitchen/Overview';
import { KitchenBookings } from './Kitchen/Bookings';

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

function AccessibilitySetup() {
  useEffect(() => {
    if (document.getElementById('vlibras-plugin')) return;
    const script = document.createElement('script');
    script.id = 'vlibras-plugin';
    script.src = 'https://vlibras.gov.br/app/vlibras-plugin.js';
    script.async = true;
    script.onerror = () => script.remove();
    document.body.appendChild(script);
  }, []);
  return null;
}

function Protected({ children, roles }) { return <ProtectedRoute allowedRoles={roles}>{children}</ProtectedRoute>; }

function NotFound() {
  return (
    <main className="auth-flow" role="status">
      <h1>Página não encontrada</h1>
      <p>O endereço que você acessou não existe ou foi movido.</p>
      <p><NavLink to="/">Voltar para a página inicial</NavLink></p>
    </main>
  );
}


function App() {
return (
    <AuthProvider>
    <ThemeProvider>
    <FavoritesProvider>
    <CartProvider>
    <AccessibilitySetup />
    <Routes>
      <Route path='/' element={<Home/>}/>
      <Route path='/catalogo' element={<Catalog/>}/>
      <Route path='/login' element={<Login/>}/>
      <Route path='/cadastro' element={<SignUp/>}/>
      <Route path='/cadastro/autenticar' element={<EmailVerification/>}/>
      <Route path='/catalogo/bancadas' element={<Protected><AgdBancada/></Protected>}/>
      <Route path='/bancada/:id' element={<Protected><Bancada/></Protected>}/>
      <Route path='/carrinho' element={<Protected roles={['customer']}><Carrinho/></Protected>}/>
      <Route path='/recuperar-senha' element={<PasswordRecovery/>}/>
      <Route path='/redefinir-senha' element={<PasswordReset/>}/>
      <Route path='/restaurante/:slug' element={<Restaurant/>}/>
      <Route path='/restaurante/:slugRest/prato/:slugPrato' element={<Dish/>}/>
      <Route path='/pedido' element={<Protected roles={['customer']}><Order/></Protected>}/>
      <Route path='/perfil' element={<Protected><Profile/></Protected>}/>
      <Route path='/configuracoes' element={<Protected><Settings/></Protected>}/>
      <Route path='/gerente' element={<Protected roles={['admin']}><Hub/></Protected>}/>
      <Route path='/gerente/estoque' element={<Protected roles={['admin']}><Stock/></Protected>}/>
      <Route path='/gerente/estoque/adicionar' element={<Protected roles={['admin']}><StockAdd/></Protected>}/>
      <Route path='/gerente/estoque/:id/editar' element={<Protected roles={['admin']}><StockAdd/></Protected>}/>
      <Route path='/gerente/dashboard' element={<Protected roles={['admin']}><Dashboard/></Protected>}/>
      <Route path='/gerente/staff' element={<Protected roles={['admin']}><Staff/></Protected>}/>
      <Route path='/gerente/imagens' element={<Protected roles={['admin']}><Images/></Protected>}/>
      <Route path='/gerente/filiacoes' element={<Protected roles={['admin']}><Affiliations/></Protected>}/>
      <Route path='/cozinha' element={<Protected roles={['cook','admin']}><Kitchen/></Protected>}/>
      <Route path='/cozinha/minhas-cozinhas' element={<Protected roles={['cook','admin']}><KitchenOverview/></Protected>}/>
      <Route path='/cozinha/pratos' element={<Protected roles={['cook','admin']}><KitchenDishes/></Protected>}/>
      <Route path='/cozinha/bancadas' element={<Protected roles={['cook','admin']}><KitchenBookings/></Protected>}/>
      <Route path='*' element={<NotFound/>}/>
    </Routes>
    </CartProvider>
    </FavoritesProvider>
    </ThemeProvider>
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

