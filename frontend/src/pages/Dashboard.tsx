import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Container,
  Typography,
  CircularProgress,
  Drawer,
  IconButton,
  useTheme,
  useMediaQuery,
  styled
} from '@mui/material';
import VoiceChat from '../components/VoiceChat/VoiceChat';
import PropertyCard from '../components/PropertyList/PropertyCard';
import { useQuery, useMutation } from 'react-query';
import axios from 'axios';

// Styled components
const StyledDrawer = styled(Drawer)(({ theme }) => ({
  '& .MuiDrawer-paper': {
    width: theme.breakpoints.values.sm,
    maxWidth: '100%',
    height: '100%',
    padding: theme.spacing(2),
    backgroundColor: theme.palette.background.paper
  }
}));

const LoadingContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'center',
  padding: theme.spacing(4)
}));

const PropertiesContainer = styled(Box)(({ theme }) => ({
  padding: theme.spacing(3)
}));

const PropertiesGrid = styled(Grid)(({ theme }) => ({
  marginTop: theme.spacing(2)
}));

interface Property {
  id: string;
  title: string;
  description: string;
  price: number;
  address: string;
  city: string;
  state: string;
  property_type: string;
  bedrooms?: number;
  bathrooms?: number;
  square_feet?: number;
  images: string[];
  features: string[];
}

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [sessionId] = useState(() => `dashboard-${Math.random().toString(36).substring(7)}`);
  const [showChatInterface, setShowChatInterface] = useState(false);
  const [favorites, setFavorites] = useState<string[]>([]);

  // Fetch recommended properties
  const { data: properties, isLoading } = useQuery<Property[]>(
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
    async ({ propertyId, type }: { propertyId: string; type: string }) => {
      await axios.post(`/api/properties/${propertyId}/interaction`, {
        session_id: sessionId,
        type
      });
    }
  );

  const handleFavorite = (propertyId: string) => {
    if (favorites.includes(propertyId)) {
      setFavorites(favorites.filter(id => id !== propertyId));
    } else {
      setFavorites([...favorites, propertyId]);
    }
    interactionMutation.mutate({ propertyId, type: 'favorite' });
  };

  const handleContact = (propertyId: string) => {
    interactionMutation.mutate({ propertyId, type: 'contact' });
    setShowChatInterface(true);
  };

  const handleVoiceMessage = async (message: string) => {
    // Update recommendations based on voice interaction
    await axios.post(`/api/conversation/${sessionId}/message`, {
      message,
      type: 'voice'
    });
  };

  const handlePropertiesUpdate = () => {
    // Update properties based on voice interaction
  };

  return (
    <>
      <Container maxWidth="xl">
        <PropertiesContainer>
          <Typography variant="h4" gutterBottom>
            Recommended Properties
          </Typography>
          
          {isLoading ? (
            <LoadingContainer>
              <CircularProgress />
            </LoadingContainer>
          ) : (
            <PropertiesGrid container spacing={3}>
              {properties?.map((property) => (
                <Grid item xs={12} sm={6} lg={4} key={property.id}>
                  <PropertyCard
                    property={property}
                    onFavorite={handleFavorite}
                    onContact={handleContact}
                    isFavorite={favorites.includes(property.id)}
                  />
                </Grid>
              ))}
            </PropertiesGrid>
          )}
        </PropertiesContainer>
      </Container>

      {/* Voice Chat Component */}
      <VoiceChat
        sessionId={sessionId}
        onMessage={handleVoiceMessage}
        onToggleInterface={(show: boolean) => setShowChatInterface(show)}
        showInterface={showChatInterface}
        onPropertiesUpdate={handlePropertiesUpdate}
      />

      {/* Chat Interface Drawer */}
      <StyledDrawer
        anchor="right"
        open={showChatInterface}
        onClose={() => setShowChatInterface(false)}
      >
        <Box height="100%" display="flex" flexDirection="column">
          <Box flex={1} overflow="auto" p={2}>
            {/* Chat messages will be rendered here by VoiceChat component */}
          </Box>
        </Box>
      </StyledDrawer>
    </> 
  );
};

export default Dashboard;
