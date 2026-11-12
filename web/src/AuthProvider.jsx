import { useEffect, useState } from 'react';
import { clearSession, login, validateSession } from './authSession';
import { AuthContext } from './authContext';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isSessionLoading, setSessionLoading] = useState(true);
  const [sessionStatus, setSessionStatus] = useState('loading');

  useEffect(() => {
    let isMounted = true;

    validateSession()
      .then((sessionUser) => {
        if (isMounted) {
          setUser(sessionUser);
          setSessionStatus(sessionUser ? 'authenticated' : 'unauthenticated');
        }
      })
      .catch(() => {
        if (isMounted) {
          setUser(null);
          setSessionStatus('unauthenticated');
        }
      })
      .finally(() => {
        if (isMounted) setSessionLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const authenticate = async (email, password) => {
    const response = await login(email, password);
    setUser(response.user);
    setSessionStatus('authenticated');
    return response;
  };

  const logout = async () => {
    await clearSession();
    setUser(null);
    setSessionStatus('unauthenticated');
  };

  return (
    <AuthContext.Provider value={{ user, isSessionLoading, sessionStatus, isAuthenticated: Boolean(user), authenticate, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
