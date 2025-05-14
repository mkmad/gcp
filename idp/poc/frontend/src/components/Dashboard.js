import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Container,
  Paper,
  Typography,
  Button,
  Box,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Stack
} from '@mui/material';

export default function Dashboard() {
  const [userData, setUserData] = useState(null);
  const [resources, setResources] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const { currentUser, logout, getIdToken } = useAuth();
  const navigate = useNavigate();
  const apiUrl = window.ENV.REACT_APP_API_URL;

  async function fetchData() {
    try {
      const token = await getIdToken();
      const headers = {
        'Authorization': `Bearer ${token}`
      };

      // Fetch user data
      const userResponse = await fetch(`${apiUrl}/api/user`, { headers });
      if (!userResponse.ok) throw new Error('Failed to fetch user data');
      const userData = await userResponse.json();
      setUserData(userData);

      // Fetch resources
      const resourcesResponse = await fetch(`${apiUrl}/api/resources`, { headers });
      if (!resourcesResponse.ok) {
        const errorData = await resourcesResponse.json();
        throw new Error(errorData.error || 'Failed to fetch resources');
      }
      const resourcesData = await resourcesResponse.json();
      setResources(resourcesData);
    } catch (error) {
      setError('Error fetching data: ' + error.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchData();
  }, []);

  async function handleLogout() {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      setError('Failed to log out: ' + error.message);
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h4" gutterBottom>
            Welcome, {currentUser?.email}
          </Typography>
          <Button
            variant="contained"
            color="secondary"
            onClick={handleLogout}
          >
            Log Out
          </Button>
        </Box>
      </Paper>

      {userData && (
        <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            User Information
          </Typography>
          <Typography>Environment: {userData.environment}</Typography>
          <Box mt={2}>
            <Typography variant="subtitle1" gutterBottom>
              Roles:
            </Typography>
            <Stack direction="row" spacing={1}>
              {userData.roles.map((role, index) => (
                <Chip
                  key={index}
                  label={role}
                  color={
                    role === 'admin' ? 'error' :
                    role === 'editor' ? 'warning' :
                    'info'
                  }
                />
              ))}
            </Stack>
          </Box>
        </Paper>
      )}

      {resources && (
        <Paper elevation={3} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Available Resources
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell>Sensitive</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {resources.resources.map((resource) => (
                  <TableRow key={resource.id}>
                    <TableCell>{resource.name}</TableCell>
                    <TableCell>{resource.description}</TableCell>
                    <TableCell>
                      <Chip
                        label={resource.sensitive_data ? 'Yes' : 'No'}
                        color={resource.sensitive_data ? 'error' : 'success'}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}
    </Container>
  );
} 