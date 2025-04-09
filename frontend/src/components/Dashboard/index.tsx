import React, { useState, useEffect } from 'react';
import { Container, Typography, Box, Grid, Paper, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import axiosInstance from '../../utils/axios';
import PropertyCard from '../PropertyList/PropertyCard';
import { useAuth } from '../../contexts/AuthContext';
import FloatingVoiceChat from '../FloatingVoiceChat/FloatingVoiceChat';

interface Property {
  id: string;
  title: string;
  description: string;
  price: number;
  address?: string;
  city: string;
  state: string;
  bedrooms?: number;
  bathrooms?: number;
  area?: number;
  images?: string[];
  features?: string[];
  property_type?: string;
  type?: string;  // For backward compatibility
  num_bedrooms?: number;  // For backward compatibility
  num_bathrooms?: number;  // For backward compatibility
  square_feet?: number;  // For backward compatibility
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated, user, logout } = useAuth();
  const [recommendations, setRecommendations] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [favorites, setFavorites] = useState<string[]>([]);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    // Fetch personalized recommendations when component mounts
    const fetchRecommendations = async () => {
      try {
        console.log('Fetching recommendations...');
        const response = await axiosInstance.get('/api/recommendations/personalized', {
          params: {
            limit: 6
          }
        });
        console.log('Recommendations response:', response.data);
        setRecommendations(response.data.recommendations);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching recommendations:', error);
        toast.error('Failed to load recommendations');
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [isAuthenticated, navigate]);

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Successfully logged out');
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
      toast.error('Failed to logout');
    }
  };

  const handlePropertiesUpdate = (updatedProperties: Property[]) => {
    console.log('Updating properties:', updatedProperties);
    if (Array.isArray(updatedProperties)) {
      setRecommendations(updatedProperties);
    } else {
      console.error('Invalid properties update:', updatedProperties);
    }
  };

  const handleFavorite = (propertyId: string) => {
    setFavorites(prev => 
      prev.includes(propertyId) 
        ? prev.filter(id => id !== propertyId)
        : [...prev, propertyId]
    );
  };

  const handleContact = (propertyId: string) => {
    toast.info(`Contact request sent for property ${propertyId}`);
  };

  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box mb={4}>
        <Grid container spacing={3} alignItems="center" justifyContent="space-between">
          <Grid item>
            <Typography variant="h4" component="h1" gutterBottom>
              Welcome{user?.email ? `, ${user.email}` : ''}
            </Typography>
          </Grid>
          <Grid item>
            <Button variant="contained" color="secondary" onClick={handleLogout}>
              Logout
            </Button>
          </Grid>
        </Grid>
      </Box>

      <Box sx={{ my: 4 }}>
        <Typography variant="h5" gutterBottom>
          {recommendations.length > 0 ? 'Properties Found' : 'Recommended Properties'}
        </Typography>
        {loading ? (
          <Typography>Loading properties...</Typography>
        ) : recommendations.length > 0 ? (
          <Grid container spacing={3}>
            {recommendations.map((property: Property) => (
              <Grid item xs={12} sm={6} md={4} key={property.id}>
                <PropertyCard 
                  property={property}
                  onFavorite={handleFavorite}
                  onContact={handleContact}
                  isFavorite={favorites.includes(property.id)}
                />
              </Grid>
            ))}
          </Grid>
        ) : (
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography>No properties available at the moment.</Typography>
          </Paper>
        )}
      </Box>

      <FloatingVoiceChat onPropertiesUpdate={handlePropertiesUpdate} />
    </Container>
  );
};

export default Dashboard;
