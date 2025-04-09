import React from 'react';
import {
  Card,
  CardContent,
  CardMedia,
  Typography,
  Box,
  IconButton,
  CardActions,
} from '@mui/material';
import {
  Favorite,
  FavoriteBorder,
  LocationOn,
  Hotel,
  Bathtub,
  SquareFoot,
  ContactMail,
} from '@mui/icons-material';

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
  square_feet?: number;
  images?: string[];
  features?: string[];
  property_type?: string;
  type?: string;  // For backward compatibility
  num_bedrooms?: number;  // For backward compatibility
  num_bathrooms?: number;  // For backward compatibility
  area?: number;  // For backward compatibility
}

interface PropertyCardProps {
  property: Property;
  onFavorite: (propertyId: string) => void;
  onContact: (propertyId: string) => void;
  isFavorite: boolean;
}

const PropertyCard: React.FC<PropertyCardProps> = ({ property, onFavorite, onContact, isFavorite }) => {
  const formatPrice = (price: number) => {
    if (price >= 10000000) {
      return `${(price / 10000000).toFixed(1)} Cr`;
    } else if (price >= 100000) {
      return `${(price / 100000).toFixed(1)} Lakh`;
    } else {
      return `₹${price.toLocaleString('en-IN')}`;
    }
  };

  // Handle both old and new property field names
  const propertyType = property.property_type || property.type || 'Not specified';
  const bedrooms = property.bedrooms || property.num_bedrooms;
  const bathrooms = property.bathrooms || property.num_bathrooms;
  const area = property.square_feet || property.area;

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardMedia
        component="img"
        height="200"
        image={property.images?.[0] || 'https://via.placeholder.com/300x200?text=No+Image'}
        alt={property.title}
      />
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography gutterBottom variant="h6" component="h2">
          {property.title}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <LocationOn fontSize="small" color="action" />
          <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
            {property.city}, {property.state}
          </Typography>
        </Box>
        <Typography variant="h6" color="primary" gutterBottom>
          {formatPrice(property.price)}
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, mb: 1 }}>
          {bedrooms && (
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Hotel fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary" sx={{ ml: 0.5 }}>
                {bedrooms} Beds
              </Typography>
            </Box>
          )}
          {bathrooms && (
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Bathtub fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary" sx={{ ml: 0.5 }}>
                {bathrooms} Baths
              </Typography>
            </Box>
          )}
          {area && (
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <SquareFoot fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary" sx={{ ml: 0.5 }}>
                {area} sq.ft
              </Typography>
            </Box>
          )}
        </Box>
        <Typography variant="body2" color="text.secondary">
          {propertyType}
        </Typography>
      </CardContent>
      <CardActions>
        <IconButton 
          onClick={() => onFavorite(property.id)} 
          color="primary"
          aria-label={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
        >
          {isFavorite ? <Favorite /> : <FavoriteBorder />}
        </IconButton>
        <IconButton 
          onClick={() => onContact(property.id)}
          color="primary"
          aria-label="Contact about property"
        >
          <ContactMail />
        </IconButton>
      </CardActions>
    </Card>
  );
};

export default PropertyCard;
