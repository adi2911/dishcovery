// SearchContext.tsx
import React, { createContext, ReactNode, useContext, useState } from 'react';
import { Recipe } from '../components/RecipeDetails';

interface SearchState {
  // all the info you'd like to persist
  results: Recipe[];       
  currentPage: number;
  totalPages: number;
  searchType: string;
  dietPreference: string;
  ingredients: string[];
  exclusions: string[];
  searchText: string;
}

interface SearchContextType {
  searchState: SearchState;
  setSearchState: React.Dispatch<React.SetStateAction<SearchState>>;
}

/** Default/initial search state */
const initialSearchState: SearchState = {
  results: [],
  currentPage: 1,
  totalPages: 1,
  searchType: 'text',
  dietPreference: 'none',
  ingredients: [],
  exclusions: [],
  searchText: '',
};

const SearchContext = createContext<SearchContextType | undefined>(undefined);

/** The provider that holds state for the entire app. */
export const SearchProvider = ({ children }: { children: ReactNode }) => {
  const [searchState, setSearchState] = useState<SearchState>(initialSearchState);

  return (
    <SearchContext.Provider value={{ searchState, setSearchState }}>
      {children}
    </SearchContext.Provider>
  );
};

/** Custom hook for consuming the context. */
export const useSearch = () => {
  const context = useContext(SearchContext);
  if (!context) {
    throw new Error('useSearch must be used within a SearchProvider');
  }
  return context;
};
