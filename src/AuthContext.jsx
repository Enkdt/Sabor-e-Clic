import { useEffect, useState } from 'react';
import { clearSession, login, validateSession } from './authSession';
import { AuthContext } from './authContext';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isSessionLoading, setSessionLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    validateSession()
      .then((sessionUser) => {
        if (isMounted) setUser(sessionUser);
      })
      .catch(() => {
        if (isMounted) setUser(null);
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
    return response;
  };

  const logout = async () => {
    await clearSession();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isSessionLoading, authenticate, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
