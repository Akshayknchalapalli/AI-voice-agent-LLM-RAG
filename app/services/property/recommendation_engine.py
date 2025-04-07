from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.property import Property
from app.models.user_preference import UserPreference
from app.services.property.vector_store import vector_store
from fastapi_cache.decorator import cache
from datetime import timedelta

class RecommendationEngine:
    def __init__(self, db: Session):
        self.db = db
        self.scaler = MinMaxScaler()
        
    def _get_property_vector(self, property_obj: Property) -> np.ndarray:
        """Convert property attributes to numerical vector"""
        return np.array([
            property_obj.price,
            len(property_obj.features),
            property_obj.square_feet or 0,
            property_obj.bedrooms or 0,
            property_obj.bathrooms or 0
        ]).reshape(1, -1)

    def _calculate_similarity_score(
        self,
        property_obj: Property,
        user_preferences: UserPreference
    ) -> float:
        """Calculate similarity score between property and user preferences"""
        # Base similarity score
        base_score = 0.0
        
        # Price match
        if user_preferences.min_price and user_preferences.max_price:
            if user_preferences.min_price <= property_obj.price <= user_preferences.max_price:
                base_score += 0.3 * user_preferences.price_range_weight
        
        # Location match
        if property_obj.city in user_preferences.preferred_locations:
            base_score += 0.2 * user_preferences.location_weight
        
        # Size match
        if user_preferences.min_bedrooms and property_obj.bedrooms:
            if property_obj.bedrooms >= user_preferences.min_bedrooms:
                base_score += 0.2 * user_preferences.size_weight
        
        # Features match
        if user_preferences.must_have_features:
            common_features = set(property_obj.features) & set(user_preferences.must_have_features)
            feature_score = len(common_features) / len(user_preferences.must_have_features)
            base_score += 0.3 * feature_score * user_preferences.features_weight
        
        return base_score

    @cache(expire=timedelta(hours=1))
    async def get_personalized_recommendations(
        self,
        session_id: str,
        limit: int = 5,
        exclude_viewed: bool = True
    ) -> List[Dict]:
        """Get personalized property recommendations for a user"""
        try:
            # Get user preferences
            user_prefs = self.db.query(UserPreference).filter(
                UserPreference.session_id == session_id
            ).first()
            
            if not user_prefs:
                # If no preferences exist, return featured properties
                return self._get_featured_properties(limit)
            
            # Get candidate properties
            query = self.db.query(Property).filter(Property.is_active == True)
            
            if exclude_viewed and user_prefs.viewed_properties:
                query = query.filter(Property.id.notin_(user_prefs.viewed_properties))
            
            # Apply basic filters from preferences
            if user_prefs.min_price:
                query = query.filter(Property.price >= user_prefs.min_price)
            if user_prefs.max_price:
                query = query.filter(Property.price <= user_prefs.max_price)
            if user_prefs.min_bedrooms:
                query = query.filter(Property.bedrooms >= user_prefs.min_bedrooms)
            if user_prefs.property_types:
                query = query.filter(Property.property_type.in_(user_prefs.property_types))
            
            candidates = query.all()
            
            # Calculate similarity scores
            property_scores = [
                (prop, self._calculate_similarity_score(prop, user_prefs))
                for prop in candidates
            ]
            
            # Sort by score and get top recommendations
            recommendations = sorted(
                property_scores,
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            # If we have semantic search context, enhance with vector search
            if user_prefs.must_have_features:
                search_query = " ".join(user_prefs.must_have_features)
                vector_results = await vector_store.search_properties(
                    query=search_query,
                    top_k=limit
                )
                
                # Combine and re-rank results
                vector_scores = {
                    int(result["id"]): result["score"]
                    for result in vector_results
                }
                
                final_scores = []
                for prop, base_score in recommendations:
                    vector_score = vector_scores.get(prop.id, 0)
                    final_score = 0.7 * base_score + 0.3 * vector_score
                    final_scores.append((prop, final_score))
                
                recommendations = sorted(
                    final_scores,
                    key=lambda x: x[1],
                    reverse=True
                )[:limit]
            
            return [prop.to_dict() for prop, _ in recommendations]
        
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return self._get_featured_properties(limit)

    def _get_featured_properties(self, limit: int = 5) -> List[Dict]:
        """Get featured properties as fallback recommendations"""
        properties = self.db.query(Property).filter(
            Property.is_active == True,
            Property.is_featured == True
        ).limit(limit).all()
        
        return [prop.to_dict() for prop in properties]

    async def update_user_preferences(
        self,
        session_id: str,
        interaction_type: str,
        property_id: int
    ):
        """Update user preferences based on interaction"""
        try:
            # Get or create user preferences
            user_prefs = self.db.query(UserPreference).filter(
                UserPreference.session_id == session_id
            ).first()
            
            if not user_prefs:
                user_prefs = UserPreference(session_id=session_id)
                self.db.add(user_prefs)
            
            # Get property data
            property_obj = self.db.query(Property).filter(
                Property.id == property_id
            ).first()
            
            if not property_obj:
                return
            
            # Update interaction history
            if interaction_type == 'view':
                if property_id not in user_prefs.viewed_properties:
                    user_prefs.viewed_properties.append(property_id)
            elif interaction_type == 'favorite':
                if property_id not in user_prefs.favorited_properties:
                    user_prefs.favorited_properties.append(property_id)
            
            # Update preference weights
            user_prefs.update_weights(interaction_type, property_obj.to_dict())
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            print(f"Error updating user preferences: {e}")

recommendation_engine = RecommendationEngine(None)  # Will be initialized with db session
