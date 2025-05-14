import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, CssBaseline, AppBar, Toolbar, Typography, Box, IconButton, Menu, MenuItem, Tooltip } from '@mui/material';
import { createTheme } from '@mui/material/styles';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LogoutIcon from '@mui/icons-material/Logout';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
  },
});

const PrivateRoute = ({ children }) => {
  const { currentUser } = useAuth();
  return currentUser ? children : <Navigate to="/login" />;
};

function App() {
  const [backendStatus, setBackendStatus] = useState('Loading...');
  const { currentUser, userDetails, logout } = useAuth() || {};
  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);

  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget);
  };
  const handleClose = () => {
    setAnchorEl(null);
  };
  const handleLogout = async () => {
    await logout();
    handleClose();
    window.location.href = '/login';
  };

  useEffect(() => {
    fetch('http://localhost:8080/health')
      .then(response => response.json())
      .then(data => {
        setBackendStatus(data.status === 'ok' ? 'Connected' : 'Error');
      })
      .catch(error => {
        console.error('Error:', error);
        setBackendStatus('Failed to connect');
      });
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <AppBar position="static" color="primary" elevation={2}>
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 700, letterSpacing: 1 }}>
              IDP POC Application
            </Typography>
            {userDetails && (
              <>
                <Typography variant="body2" sx={{ mr: 2 }}>
                  {userDetails.email} ({userDetails.roles && userDetails.roles.join(', ')})
                </Typography>
                <Tooltip title="Logout">
                  <IconButton color="inherit" onClick={handleMenu} size="large">
                    <LogoutIcon />
                  </IconButton>
                </Tooltip>
                <Menu
                  anchorEl={anchorEl}
                  open={open}
                  onClose={handleClose}
                  anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                  transformOrigin={{ vertical: 'top', horizontal: 'right' }}
                >
                  <MenuItem onClick={handleLogout}>Logout</MenuItem>
                </Menu>
              </>
            )}
          </Toolbar>
        </AppBar>
        <Box sx={{ p: 2 }}>
        </Box>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <Dashboard />
                </PrivateRoute>
              }
            />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App; 