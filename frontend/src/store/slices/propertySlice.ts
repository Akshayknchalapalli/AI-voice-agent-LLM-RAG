import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

interface Property {
  id: number;
  title: string;
  description: string;
  price: number;
  // ... other property fields
}

interface PropertyState {
  recommendations: Property[];
  favorites: number[];
  loading: boolean;
  error: string | null;
}

const initialState: PropertyState = {
  recommendations: [],
  favorites: [],
  loading: false,
  error: null
};

export const fetchRecommendations = createAsyncThunk(
  'property/fetchRecommendations',
  async (sessionId: string) => {
    const response = await axios.get(`/api/properties/recommendations?session_id=${sessionId}`);
    return response.data;
  }
);

export const interactWithProperty = createAsyncThunk(
  'property/interact',
  async ({ propertyId, type, sessionId }: { propertyId: number; type: string; sessionId: string }) => {
    await axios.post(`/api/properties/${propertyId}/interaction`, {
      session_id: sessionId,
      type
    });
    return propertyId;
  }
);

const propertySlice = createSlice({
  name: 'property',
  initialState,
  reducers: {
    toggleFavorite: (state, action) => {
      const propertyId = action.payload;
      if (state.favorites.includes(propertyId)) {
        state.favorites = state.favorites.filter(id => id !== propertyId);
      } else {
        state.favorites.push(propertyId);
      }
    },
    clearRecommendations: (state) => {
      state.recommendations = [];
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchRecommendations.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRecommendations.fulfilled, (state, action) => {
        state.loading = false;
        state.recommendations = action.payload;
      })
      .addCase(fetchRecommendations.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch recommendations';
      });
  }
});

export const { toggleFavorite, clearRecommendations } = propertySlice.actions;
export default propertySlice.reducer;
