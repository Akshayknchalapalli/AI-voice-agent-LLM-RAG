import React from 'react';
import {
  Card,
  CardContent,
  CardMedia,
  Typography,
  Box,
  Chip,
  IconButton,
  CardActions,
} from '@mui/material';
import {
  Favorite,
  FavoriteBorder,
  Phone,
  LocationOn,
  KingBed,
  Bathtub,
  SquareFoot,
} from '@mui/icons-material';

interface PropertyCardProps {
  property: {
    id: number;
    title: string;
    description: string;
    price: number;
    address: string;
    city: string;
    state: string;
    bedrooms: number;
    bathrooms: number;
    square_feet: number;
    images: string[];
    features: string[];
    property_type: string;
  };
  onFavorite: (id: number) => void;
  onContact: (id: number) => void;
  isFavorite: boolean;
}

const PropertyCard: React.FC<PropertyCardProps> = ({
  property,
  onFavorite,
  onContact,
  isFavorite,
}) => {
  return (
    <Card elevation={3} sx={{ maxWidth: 345, m: 2 }}>
      <CardMedia
        component="img"
        height="200"
        image={property.images[0] || '/placeholder.jpg'}
        alt={property.title}
      />
      <CardContent>
        <Typography gutterBottom variant="h6" component="div">
          {property.title}
        </Typography>
        
        <Typography variant="h5" color="primary" gutterBottom>
          ${property.price.toLocaleString()}
        </Typography>

        <Box display="flex" alignItems="center" gap={1} mb={1}>
          <LocationOn color="action" fontSize="small" />
          <Typography variant="body2" color="text.secondary">
            {`${property.city}, ${property.state}`}
          </Typography>
        </Box>

        <Box display="flex" gap={2} mb={2}>
          <Box display="flex" alignItems="center">
            <KingBed color="action" fontSize="small" />
            <Typography variant="body2" ml={0.5}>
              {property.bedrooms} beds
            </Typography>
          </Box>
          <Box display="flex" alignItems="center">
            <Bathtub color="action" fontSize="small" />
            <Typography variant="body2" ml={0.5}>
              {property.bathrooms} baths
            </Typography>
          </Box>
          <Box display="flex" alignItems="center">
            <SquareFoot color="action" fontSize="small" />
            <Typography variant="body2" ml={0.5}>
              {property.square_feet} sqft
            </Typography>
          </Box>
        </Box>

        <Box display="flex" flexWrap="wrap" gap={0.5} mb={2}>
          {property.features.slice(0, 3).map((feature, index) => (
            <Chip
              key={index}
              label={feature}
              size="small"
              variant="outlined"
              color="primary"
            />
          ))}
        </Box>

        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          {property.description}
        </Typography>
      </CardContent>

      <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
        <IconButton
          onClick={() => onFavorite(property.id)}
          color={isFavorite ? 'error' : 'default'}
        >
          {isFavorite ? <Favorite /> : <FavoriteBorder />}
        </IconButton>
        <IconButton
          onClick={() => onContact(property.id)}
          color="primary"
        >
          <Phone />
        </IconButton>
      </CardActions>
    </Card>
  );
};

export default PropertyCard;
