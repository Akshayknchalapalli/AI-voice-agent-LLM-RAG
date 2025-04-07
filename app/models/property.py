from sqlalchemy import Column, Integer, String, Float, JSON, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.models.base import TimestampedBase
import enum

class PropertyType(str, enum.Enum):
    HOUSE = "house"
    APARTMENT = "apartment"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    LAND = "land"

class ListingType(str, enum.Enum):
    SALE = "sale"
    RENT = "rent"

class Property(TimestampedBase):
    __tablename__ = "properties"

    # Basic Information
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    property_type = Column(Enum(PropertyType), nullable=False)
    listing_type = Column(Enum(ListingType), nullable=False)
    
    # Location
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Details
    price = Column(Integer, nullable=False)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    square_feet = Column(Integer)
    lot_size = Column(Float)
    year_built = Column(Integer)
    
    # Features
    features = Column(JSON, default=list)  # List of amenities/features
    
    # Media
    images = Column(JSON, default=list)  # List of image URLs
    virtual_tour_url = Column(String)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Vector embedding for semantic search
    vector_id = Column(String, unique=True)  # ID in vector database
    
    def to_dict(self):
        """Convert property to dictionary format"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "property_type": self.property_type.value,
            "listing_type": self.listing_type.value,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "price": self.price,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "square_feet": self.square_feet,
            "lot_size": self.lot_size,
            "year_built": self.year_built,
            "features": self.features,
            "images": self.images,
            "virtual_tour_url": self.virtual_tour_url,
            "is_active": self.is_active,
            "is_featured": self.is_featured
        }

    def to_embedding_text(self):
        """Convert property to text format for embedding"""
        features_text = ", ".join(self.features) if self.features else ""
        return f"""
        {self.title}. {self.description}
        {self.property_type.value.title()} for {self.listing_type.value}
        Located in {self.city}, {self.state}
        Price: ${self.price:,}
        {self.bedrooms} bedrooms, {self.bathrooms} bathrooms
        {self.square_feet} square feet
        Features: {features_text}
        """
