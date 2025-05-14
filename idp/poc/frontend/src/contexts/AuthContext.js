import React, { createContext, useState, useContext, useEffect } from 'react';
import { getCurrentUser, loginWithEmail, logout } from '../firebase';

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      try {
        const currentUser = await getCurrentUser();
        if (currentUser) {
          const token = await currentUser.getIdToken();
          setUser(currentUser);
          setToken(token);
        }
      } catch (error) {
        console.error('Auth initialization failed:', error);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (email, password) => {
    const { user, token } = await loginWithEmail(email, password);
    setUser(user);
    setToken(token);
    return { user, token };
  };

  const logoutUser = async () => {
    await logout();
    setUser(null);
    setToken(null);
  };

  const value = {
    user,
    token,
    login,
    logout: logoutUser,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}; 