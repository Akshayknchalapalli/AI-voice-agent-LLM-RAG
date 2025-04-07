from sqlalchemy import Column, Integer, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import TimestampedBase
import numpy as np

class UserPreference(TimestampedBase):
    __tablename__ = "user_preferences"

    # Session or user identifier
    session_id = Column(String, unique=True, nullable=False)
    
    # Explicit preferences
    min_price = Column(Integer, nullable=True)
    max_price = Column(Integer, nullable=True)
    min_bedrooms = Column(Integer, nullable=True)
    min_bathrooms = Column(Float, nullable=True)
    preferred_locations = Column(JSON, default=list)  # List of preferred cities/areas
    property_types = Column(JSON, default=list)  # List of preferred property types
    must_have_features = Column(JSON, default=list)  # List of required features
    
    # Implicit preferences (learned from interactions)
    price_range_weight = Column(Float, default=1.0)
    location_weight = Column(Float, default=1.0)
    size_weight = Column(Float, default=1.0)
    features_weight = Column(Float, default=1.0)
    
    # Interaction history
    viewed_properties = Column(JSON, default=list)  # List of viewed property IDs
    favorited_properties = Column(JSON, default=list)  # List of favorited property IDs
    interaction_counts = Column(JSON, default=dict)  # Count of interactions by type
    
    def update_weights(self, interaction_type: str, property_data: dict):
        """Update preference weights based on user interactions"""
        # Initialize interaction counts if not exists
        if not self.interaction_counts:
            self.interaction_counts = {}
        
        # Update interaction count
        self.interaction_counts[interaction_type] = self.interaction_counts.get(interaction_type, 0) + 1
        
        # Update weights based on interaction type
        if interaction_type in ['view', 'favorite', 'inquire']:
            # Increase weight for price range if user interacts with properties in similar price range
            if self.min_price and self.max_price:
                if self.min_price <= property_data['price'] <= self.max_price:
                    self.price_range_weight *= 1.1
            
            # Increase weight for location if user interacts with properties in preferred locations
            if property_data['city'] in self.preferred_locations:
                self.location_weight *= 1.1
            
            # Increase weight for size if user interacts with properties of similar size
            if self.min_bedrooms and property_data['bedrooms'] >= self.min_bedrooms:
                self.size_weight *= 1.1
            
            # Increase weight for features if property has preferred features
            common_features = set(property_data['features']) & set(self.must_have_features)
            if common_features:
                self.features_weight *= 1.1

    def get_preference_vector(self) -> np.ndarray:
        """Convert preferences to a numerical vector for similarity calculations"""
        return np.array([
            self.price_range_weight,
            self.location_weight,
            self.size_weight,
            self.features_weight
        ])
