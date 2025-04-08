import React, { useState } from 'react';
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
} from '@mui/icons-material';

interface PropertyCardProps {
  id: number;
  title: string;
  description: string;
  price: string;
  location: string;
  imageUrl: string;
}

const PropertyCard: React.FC<PropertyCardProps> = ({
  id,
  title,
  description,
  price,
  location,
  imageUrl,
}) => {
  const [isFavorite, setIsFavorite] = useState(false);

  const handleFavorite = () => {
    setIsFavorite(!isFavorite);
  };

  const handleContact = () => {
    // You can implement contact functionality here
    console.log('Contact clicked for property:', id);
  };

  return (
    <Card elevation={3} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardMedia
        component="img"
        height="200"
        image={imageUrl}
        alt={title}
        sx={{ objectFit: 'cover' }}
      />
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography gutterBottom variant="h6" component="div" noWrap>
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
        }}>
          {description}
        </Typography>
        <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <LocationOn color="action" fontSize="small" />
          <Typography variant="body2" color="text.secondary">
            {location}
          </Typography>
        </Box>
        <Typography variant="h6" color="primary" sx={{ mt: 1 }}>
          {price}
        </Typography>
      </CardContent>
      <CardActions sx={{ justifyContent: 'space-between', p: 2 }}>
        <IconButton 
          onClick={handleFavorite}
          color={isFavorite ? "error" : "default"}
          aria-label="add to favorites"
        >
          {isFavorite ? <Favorite /> : <FavoriteBorder />}
        </IconButton>
        <IconButton onClick={handleContact} color="primary" aria-label="contact">
          <Phone />
        </IconButton>
      </CardActions>
    </Card>
  );
};

export default PropertyCard;
