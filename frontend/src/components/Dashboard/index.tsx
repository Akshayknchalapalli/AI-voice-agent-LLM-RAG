import React, { useState } from 'react';
import { Container, Typography, Box, Button, Grid, Paper } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import axios from 'axios';
import VoiceChat from '../VoiceChat/VoiceChat';
import PropertyCard from '../PropertyList/PropertyCard';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const [showVoiceChat, setShowVoiceChat] = useState(false);

  // Sample property data - replace with actual API call
  const sampleProperties = [
    {
      id: 1,
      title: "Modern Downtown Apartment",
      description: "Beautiful 2 bedroom apartment with stunning city views and modern amenities",
      price: "$250,000",
      location: "Downtown, City Center",
      imageUrl: "https://placehold.co/600x400/png?text=Modern+Apartment"
    },
    {
      id: 2,
      title: "Suburban Family Home",
      description: "Spacious 4 bedroom house with large backyard and updated kitchen",
      price: "$450,000",
      location: "Peaceful Suburbs",
      imageUrl: "https://placehold.co/600x400/png?text=Family+Home"
    },
    {
      id: 3,
      title: "Luxury Penthouse",
      description: "Exclusive penthouse with panoramic views and high-end finishes",
      price: "$850,000",
      location: "City Center",
      imageUrl: "https://placehold.co/600x400/png?text=Luxury+Penthouse"
    },
    {
      id: 4,
      title: "Cozy Studio Apartment",
      description: "Perfect starter home or investment property in prime location",
      price: "$150,000",
      location: "University District",
      imageUrl: "https://placehold.co/600x400/png?text=Studio+Apartment"
    }
  ];

  const handleLogout = async () => {
    try {
      await axios.post('/api/auth/logout');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      toast.success('Successfully logged out');
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout error:', error);
      toast.error('Error during logout');
    }
  };

  const toggleVoiceChat = () => {
    setShowVoiceChat(!showVoiceChat);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Grid container spacing={3}>
        {/* Header Section */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Box>
                <Typography variant="h4" component="h1" gutterBottom>
                  Welcome Back!
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Hello, {user.email}
                </Typography>
              </Box>
              <Button variant="outlined" color="primary" onClick={handleLogout}>
                Logout
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Voice Chat Section */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h5">AI Voice Assistant</Typography>
              <Button 
                variant="contained" 
                color={showVoiceChat ? "secondary" : "primary"}
                onClick={toggleVoiceChat}
              >
                {showVoiceChat ? "Close Voice Chat" : "Start Voice Chat"}
              </Button>
            </Box>
            {showVoiceChat && <VoiceChat />}
          </Paper>
        </Grid>

        {/* Property Listings */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Featured Properties
            </Typography>
            <Grid container spacing={3}>
              {sampleProperties.map((property) => (
                <Grid item xs={12} sm={6} md={3} key={property.id}>
                  <PropertyCard {...property} />
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;
