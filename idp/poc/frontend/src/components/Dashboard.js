import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Container, 
  Paper, 
  Typography, 
  Button, 
  Box,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  Alert
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import CloseIcon from '@mui/icons-material/Close';

export default function Dashboard() {
  const navigate = useNavigate();
  const { logout, currentUser, userDetails, gcpIamRoles, handleRemoveRole } = useAuth();
  const [resources, setResources] = useState([]);
  const [accessSummary, setAccessSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchResources = async () => {
      if (!currentUser || !currentUser.token) return;
      setLoading(true);
      setError('');
      try {
        const res = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8080'}/api/resources`, {
          headers: { Authorization: `Bearer ${currentUser.token}` },
        });
        if (!res.ok) {
          const err = await res.json();
          setError(err.error || 'Failed to fetch resources');
          setResources([]);
        } else {
          const data = await res.json();
          setResources(data.resources || []);
          setAccessSummary(data.access_summary || null);
        }
      } catch (e) {
        setError('Failed to fetch resources');
        setResources([]);
      }
      setLoading(false);
    };
    fetchResources();
  }, [currentUser]);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Failed to log out:', error);
    }
  };

  const getAccessLevelColor = (level) => {
    switch (level) {
      case 'Highly Sensitive': return 'error';
      case 'Editor Access': return 'warning';
      case 'General Access': return 'success';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
      <Box sx={{ width: '100%', maxWidth: 1200 }}>
        <Paper elevation={6} sx={{ p: 4, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h4" component="h1">
              Resource Dashboard
            </Typography>
            <Button variant="contained" color="primary" onClick={handleLogout}>
              Logout
            </Button>
          </Box>

          {userDetails && (
            <Alert severity="info" sx={{ mb: 3 }}>
              You are logged in as <strong>{userDetails.email}</strong> with roles: <strong>{userDetails.roles && userDetails.roles.join(', ')}</strong> in <strong>{userDetails.environment}</strong> environment.
            </Alert>
          )}

          {accessSummary && (
            <Paper variant="outlined" sx={{ p: 2, mb: 3, bgcolor: 'background.default' }}>
              <Typography variant="h6" gutterBottom>Access Summary</Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2">Access Level: <Chip label={accessSummary.access_level} color="primary" size="small" /></Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2">Total Resources: {accessSummary.total_resources}</Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2">Sensitive Access: {accessSummary.has_sensitive_access ? '✓' : '✗'}</Typography>
                </Grid>
              </Grid>
            </Paper>
          )}

          {loading ? (
            <Typography>Loading resources...</Typography>
          ) : error ? (
            <Alert severity="error">{error}</Alert>
          ) : resources.length === 0 ? (
            <Alert severity="info">No resources available for your access level.</Alert>
          ) : (
            <Grid container spacing={3}>
              {resources.map((r) => (
                <Grid item xs={12} sm={6} md={4} key={r.id}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {r.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" paragraph>
                        {r.description}
                      </Typography>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Chip 
                          label={r.access_level}
                          size="small"
                          color={getAccessLevelColor(r.access_level)}
                        />
                        {r.sensitive_data && (
                          <Chip 
                            label="Sensitive"
                            size="small"
                            color="error"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </Paper>
        {gcpIamRoles && gcpIamRoles.length > 0 && (
          <Paper elevation={6} variant="outlined" sx={{ p: 2, mb: 3, width: '100%' }}>
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
        )}
      </Box>
    </Box>
  );
} 