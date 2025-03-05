import React, { createContext, ReactNode, useContext, useState } from 'react';
import { Recipe } from '../components/RecipeDetails';

interface SearchState {
  results: Recipe[];
  currentPage: number;
  totalPages: number;
  searchType: string;
  dietPreference: string;
  ingredients: string[];
  exclusions: string[];
  searchText: string;
  error: boolean;
}

interface SearchContextType {
  searchState: SearchState;
  setSearchState: React.Dispatch<React.SetStateAction<SearchState>>;
}

const initialSearchState: SearchState = {
  results: [],
  currentPage: 1,
  totalPages: 1,
  searchType: 'text',
  dietPreference: 'none',
  ingredients: [],
  exclusions: [],
  searchText: '',
  error: false, 
};

const SearchContext = createContext<SearchContextType | undefined>(undefined);

export const SearchProvider = ({ children }: { children: ReactNode }) => {
  const [searchState, setSearchState] = useState<SearchState>(initialSearchState);

  return (
    <SearchContext.Provider value={{ searchState, setSearchState }}>
      {children}
    </SearchContext.Provider>
  );
};

export const useSearch = () => {
  const context = useContext(SearchContext);
  if (!context) {
    throw new Error('useSearch must be used within a SearchProvider');
  }
  return context;
};
