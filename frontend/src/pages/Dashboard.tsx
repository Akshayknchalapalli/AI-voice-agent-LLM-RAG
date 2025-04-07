import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Container,
  Typography,
  CircularProgress,
  Drawer,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import VoiceChat from '../components/VoiceChat/VoiceChat';
import PropertyCard from '../components/PropertyList/PropertyCard';
import { useQuery, useMutation } from 'react-query';
import axios from 'axios';

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [sessionId] = useState(() => crypto.randomUUID());
  const [showChat, setShowChat] = useState(!isMobile);
  const [favorites, setFavorites] = useState<number[]>([]);

  // Fetch recommended properties
  const { data: properties, isLoading } = useQuery(
    ['recommendations', sessionId],
    async () => {
      const response = await axios.get(`/api/properties/recommendations?session_id=${sessionId}`);
      return response.data;
    },
    {
      refetchInterval: 30000 // Refresh every 30 seconds
    }
  );

  // Handle property interactions
  const interactionMutation = useMutation(
    async ({ propertyId, type }: { propertyId: number; type: string }) => {
      await axios.post(`/api/properties/${propertyId}/interaction`, {
        session_id: sessionId,
        type
      });
    }
  );

  const handleFavorite = (propertyId: number) => {
    if (favorites.includes(propertyId)) {
      setFavorites(favorites.filter(id => id !== propertyId));
    } else {
      setFavorites([...favorites, propertyId]);
    }
    interactionMutation.mutate({ propertyId, type: 'favorite' });
  };

  const handleContact = (propertyId: number) => {
    interactionMutation.mutate({ propertyId, type: 'contact' });
    setShowChat(true);
  };

  const handleVoiceMessage = async (message: string) => {
    // Update recommendations based on voice interaction
    await axios.post(`/api/conversation/${sessionId}/message`, {
      message,
      type: 'voice'
    });
  };

  return (
    <Container maxWidth="xl">
      <Grid container spacing={3}>
        {/* Main Content */}
        <Grid item xs={12} md={showChat ? 8 : 12}>
          <Box py={3}>
            <Typography variant="h4" gutterBottom>
              Recommended Properties
            </Typography>
            
            {isLoading ? (
              <Box display="flex" justifyContent="center" py={4}>
                <CircularProgress />
              </Box>
            ) : (
              <Grid container spacing={2}>
                {properties?.map((property: any) => (
                  <Grid item xs={12} sm={6} lg={4} key={property.id}>
                    <PropertyCard
                      property={property}
                      onFavorite={handleFavorite}
                      onContact={handleContact}
                      isFavorite={favorites.includes(property.id)}
                    />
                  </Grid>
                ))}
              </Grid>
            )}
          </Box>
        </Grid>

        {/* Voice Chat Drawer/Sidebar */}
        {isMobile ? (
          <Drawer
            anchor="right"
            open={showChat}
            onClose={() => setShowChat(false)}
            sx={{ width: 350 }}
          >
            <Box width={350}>
              <VoiceChat
                sessionId={sessionId}
                onMessage={handleVoiceMessage}
              />
            </Box>
          </Drawer>
        ) : (
          showChat && (
            <Grid item md={4}>
              <VoiceChat
                sessionId={sessionId}
                onMessage={handleVoiceMessage}
              />
            </Grid>
          )
        )}
      </Grid>
    </Container>
  );
};

export default Dashboard;
