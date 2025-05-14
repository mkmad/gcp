import React, { createContext, useContext, useState, useEffect } from 'react';
import { 
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged
} from 'firebase/auth';
import { auth, loginWithGoogle } from '../firebase';
import { Paper, Typography, Chip, Box, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [userDetails, setUserDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [gcpIamRoles, setGcpIamRoles] = useState([]);

  useEffect(() => {
    // Subscribe to auth state changes
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (user) {
        // Get the ID token
        const token = await user.getIdToken();
        // Fetch user details from backend
        try {
          const res = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8080'}/api/user`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          const data = await res.json();
          setUserDetails(data);
        } catch (e) {
          setUserDetails(null);
        }
        setCurrentUser({ user, token });
      } else {
        setCurrentUser(null);
        setUserDetails(null);
      }
      setLoading(false);
    });

    // Cleanup subscription
    return unsubscribe;
  }, []);

  useEffect(() => {
    const fetchIamRoles = async () => {
      if (!currentUser || !currentUser.token) return;
      const res = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8080'}/api/iam-roles`, {
        headers: { Authorization: `Bearer ${currentUser.token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setGcpIamRoles(data.gcp_iam_roles || []);
      }
    };
    fetchIamRoles();
  }, [currentUser]);

  const login = async (email, password) => {
    try {
      const result = await signInWithEmailAndPassword(auth, email, password);
      const token = await result.user.getIdToken();
      return { user: result.user, token };
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await signOut(auth);
      setCurrentUser(null);
      setUserDetails(null);
      // Optionally, force reload:
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout error:', error);
      throw error;
    }
  };

  // Handler to remove a role from the local display (demo only)
  const handleRemoveRole = (roleToRemove) => {
    setGcpIamRoles((prev) => prev.filter(role => role !== roleToRemove));
  };

  const value = {
    currentUser,
    userDetails,
    login,
    logout,
    loginWithGoogle,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
      {gcpIamRoles.length > 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'center' }}>
          <Paper variant="outlined" sx={{ p: 2, mb: 3, width: '100%', maxWidth: 1200 }}>
            <Typography variant="h6" gutterBottom>GCP IAM Roles</Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {gcpIamRoles.map(role => (
                <Chip
                  key={role}
                  label={role}
                  size="small"
                  onDelete={() => handleRemoveRole(role)}
                  deleteIcon={<CloseIcon />}
                  sx={{ m: 0.5 }}
                />
              ))}
            </Box>
          </Paper>
        </Box>
      )}
    </AuthContext.Provider>
  );
} 