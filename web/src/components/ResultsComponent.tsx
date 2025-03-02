import { Menu } from '@headlessui/react';
import React, { useRef } from 'react';
import { useSearch } from '../store/SearchContext';
import AutoComplete from './AutoComplete';
import { Recipe } from './RecipeDetails';
import './SearchComponent.css'; // Keep the original stylesheet

interface ResultsComponentProps {
  timeTaken: number;
  searchType: string;
  setSearchType: (value: string) => void;
  dietPreference: string;
  setDietPreference: (value: string) => void;

  ingredients: string[];
  addIngredient: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  removeIngredient: (index: number) => void;

  exclusions: string[];
  addExclusion: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  removeExclusion: (index: number) => void;

  searchText: string;
  setSearchText: (value: string) => void;

  handleSearch: () => void;

  results: Recipe[];
  currentPage: number;
  totalPages: number;
  goToNextPage: () => void;
  goToPrevPage: () => void;

  currentPageResults: Recipe[];
  handleRecipeClick: (recipeId: string) => void;
}

const ResultsComponent: React.FC<ResultsComponentProps> = ({
  timeTaken,
  searchType,
  setSearchType,
  dietPreference,
  setDietPreference,
  ingredients,
  addIngredient,
  removeIngredient,
  exclusions,
  addExclusion,
  removeExclusion,
  searchText,
  setSearchText,
  handleSearch,
  results,
  currentPage,
  totalPages,
  goToNextPage,
  goToPrevPage,
  currentPageResults,
  handleRecipeClick,
}) => {
  const { setSearchState } = useSearch();

  // Snapshot of initial search fields, to detect changes
  const initialRef = useRef({
    searchType,
    dietPreference,
    ingredients: [...ingredients],
    exclusions: [...exclusions],
    searchText,
  });

  const fieldsChanged = (): boolean => {
    const init = initialRef.current;
    if (init.searchType !== searchType) return true;
    if (init.dietPreference !== dietPreference) return true;
    if (init.searchText !== searchText) return true;

    if (
      init.ingredients.length !== ingredients.length ||
      init.ingredients.some((val, i) => val !== ingredients[i])
    ) {
      return true;
    }
    if (
      init.exclusions.length !== exclusions.length ||
      init.exclusions.some((val, i) => val !== exclusions[i])
    ) {
      return true;
    }
    return false;
  };


  function formatDuration(milliseconds: number): string {
    // If it's under 1 second, show ms
    if (milliseconds < 1000) {
      return `${milliseconds.toFixed(2)} ms`;
    }
  
    // Convert to seconds
    const totalSeconds = milliseconds / 1000;
  
    // If it's under 1 minute, show in seconds
    if (totalSeconds < 60) {
      return `${totalSeconds.toFixed(2)} s`;
    }
  
    // Otherwise, show minutes:seconds
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = (totalSeconds % 60).toFixed(2);
    return `${minutes} min ${seconds} s`;
  }

  const searchDuration = formatDuration(timeTaken)

  // On Enter, search only if fields changed, and only if the user
  // is NOT typing something in an ingredient/exclusion input.
  const handleGlobalKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter') {
      const activeEl = document.activeElement as HTMLInputElement | null;
      if (!activeEl) {
        // No focused element => run search if changed
        if (fieldsChanged()) {
          handleSearch();
          // Update snapshot
          initialRef.current = {
            searchType,
            dietPreference,
            ingredients: [...ingredients],
            exclusions: [...exclusions],
            searchText,
          };
        }
        return;
      }

      const nameAttr = activeEl.getAttribute('name');
      if (nameAttr === 'ingredientInput' || nameAttr === 'exclusionInput') {
        // If the user typed something, let the input’s onKeyDown handle it => do nothing
        // If empty, run search if changed
        if (!activeEl.value.trim()) {
          if (fieldsChanged()) {
            handleSearch();
            initialRef.current = {
              searchType,
              dietPreference,
              ingredients: [...ingredients],
              exclusions: [...exclusions],
              searchText,
            };
          }
        }
      } else {
        // Not in ingredient/exclusion => run search if changed
        if (fieldsChanged()) {
          handleSearch();
          initialRef.current = {
            searchType,
            dietPreference,
            ingredients: [...ingredients],
            exclusions: [...exclusions],
            searchText,
          };
        }
      }
    }
  };

  const clearSearch = () => {
    setSearchState((prev) => ({
      ...prev,
      results: [],
      currentPage: 1,
      totalPages: 1,
      searchText: '',
      ingredients: [],
      exclusions: [],
      searchType: 'text',
      dietPreference: 'none',
    }));
  };

  return (
    <div
      className="results-mode-container text-white p-4"
      tabIndex={0}
      onKeyDown={handleGlobalKeyDown}
    >
      <div className="top-filters flex flex-wrap items-start gap-4 mb-6">
        <div className="filter-item flex flex-col">
          <label className="filter-label">Search Type</label>
          <Menu as="div" className="relative inline-block w-full">
            <Menu.Button className="dropdown-button">
              {searchType === 'text' ? 'Search by Text' : 'Search by Ingredients'}
            </Menu.Button>
            <Menu.Items className="dropdown-menu">
              <Menu.Item>
                {({ active }) => (
                  <button
                    className={`dropdown-item ${active ? 'bg-gray-600' : ''}`}
                    onClick={() => setSearchType('text')}
                  >
                    Search by Text
                  </button>
                )}
              </Menu.Item>
              <Menu.Item>
                {({ active }) => (
                  <button
                    className={`dropdown-item ${active ? 'bg-gray-600' : ''}`}
                    onClick={() => setSearchType('ingredients')}
                  >
                    Search by Ingredients
                  </button>
                )}
              </Menu.Item>
            </Menu.Items>
          </Menu>
        </div>

        {/* Diet Preference */}
        <div className="filter-item flex flex-col">
          <label className="filter-label">Diet Preference</label>
          <Menu as="div" className="relative inline-block w-full">
            <Menu.Button className="dropdown-button">
              {dietPreference === 'none'
                ? 'No Preference'
                : dietPreference.charAt(0).toUpperCase() + dietPreference.slice(1)}
            </Menu.Button>
            <Menu.Items className="dropdown-menu">
              <Menu.Item>
                {({ active }) => (
                  <button
                    className={`dropdown-item ${active ? 'bg-gray-600' : ''}`}
                    onClick={() => setDietPreference('none')}
                  >
                    No Preference
                  </button>
                )}
              </Menu.Item>
              <Menu.Item>
                {({ active }) => (
                  <button
                    className={`dropdown-item ${active ? 'bg-gray-600' : ''}`}
                    onClick={() => setDietPreference('vegan')}
                  >
                    Vegan
                  </button>
                )}
              </Menu.Item>
              <Menu.Item>
                {({ active }) => (
                  <button
                    className={`dropdown-item ${active ? 'bg-gray-600' : ''}`}
                    onClick={() => setDietPreference('vegetarian')}
                  >
                    Vegetarian
                  </button>
                )}
              </Menu.Item>
              <Menu.Item>
                {({ active }) => (
                  <button
                    className={`dropdown-item ${active ? 'bg-gray-600' : ''}`}
                    onClick={() => setDietPreference('gluten-free')}
                  >
                    Gluten-Free
                  </button>
                )}
              </Menu.Item>
            </Menu.Items>
          </Menu>
        </div>

        {/* Ingredients vs Text */}
        {searchType === 'ingredients' ? (
          <div className="filter-item flex flex-col">
            <label className="filter-label">Ingredients</label>
            <AutoComplete
              onAddIngredient={(ingredient) => {
                if (ingredient.trim()) {
                  // Create a synthetic keydown event for addIngredient()
                  const syntheticEvent = {
                    key: 'Enter',
                    target: { value: ingredient },
                    preventDefault: () => {},
                  } as unknown as React.KeyboardEvent<HTMLInputElement>;
                  addIngredient(syntheticEvent);
                }
              }}
            />
          </div>
        ) : (
          <div className="filter-item flex flex-col">
            <label className="filter-label">Search Text</label>
            <input
              type="text"
              placeholder="Type your search here..."
              className="filter-input"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
          </div>
        )}

        {/* Exclusions */}
        <div className="filter-item flex flex-col">
          <label className="filter-label">Exclusions</label>
          <input
            type="text"
            name="exclusionInput"
            placeholder="Exclude items, press Enter"
            className="filter-input"
            onKeyDown={addExclusion}
          />
        </div>

        {/* Re-Search Button */}
        <div className="filter-item flex flex-col">
          <label className="filter-label" style={{ visibility: 'hidden' }}>
            &nbsp;
          </label>
          <button className="search-btn" onClick={handleSearch}>
            Search
          </button>
        </div>

        {/* Summary (optional text) */}
        <div className="filter-item flex flex-col">
          <label className="filter-label" style={{ visibility: 'hidden' }}>
            &nbsp;
          </label>
          <span className="text-sm text-gray-300">
            {searchType === 'text'
              ? `Searched for text: ${searchText || '(none)'}`
              : `Searched for ingredients: ${
                  ingredients.length > 0 ? ingredients.join(', ') : '(none)'
                }`}
                {`Fetched results in : ${searchDuration}`}
          </span>
        </div>

        {/* Clear Search */}
        <div className="filter-item flex flex-col">
          <label className="filter-label" style={{ visibility: 'hidden' }}>
            &nbsp;
          </label>
          <button className="clear-btn" onClick={clearSearch}>
            Clear Search
          </button>
        </div>
      </div>

      {/* Chips for Ingredients + Exclusions */}
      {searchType === 'ingredients' && ingredients.length > 0 && (
        <div className="chips-row">
          <strong className="chips-label">Ingredients:</strong>
          {ingredients.map((ing, idx) => (
            <div key={idx} className="chip-item">
              {ing}
              <button
                onClick={() => removeIngredient(idx)}
                className="chip-close-btn"
              >
                ✖
              </button>
            </div>
          ))}
        </div>
      )}

      {exclusions.length > 0 && (
        <div className="chips-row">
          <strong className="chips-label">Exclusions:</strong>
          {exclusions.map((ex, idx) => (
            <div key={idx} className="chip-item">
              {ex}
              <button
                onClick={() => removeExclusion(idx)}
                className="chip-close-btn"
              >
                ✖
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Results + Pagination */}
      <div className="results-container mt-6">
        {currentPageResults.map((recipe) => {
          const instructionSnippet =
            recipe.instructions.length > 80
              ? recipe.instructions.slice(0, 80) + '...'
              : recipe.instructions;
          const ingredientHighlights = recipe.ingredients.slice(0, 3).join(', ');
          const ingredientsSnippet =
            recipe.ingredients.length > 3
              ? `${ingredientHighlights}...`
              : ingredientHighlights;

          return (
            <div
              key={recipe.id}
              className="result-item"
              onClick={() => handleRecipeClick(recipe.id)}
            >
              <h3 className="result-title">{recipe.title}</h3>
              <p className="result-subtitle">
                <strong>Ingredients:</strong> {ingredientsSnippet}
              </p>
              <p className="result-snippet">
                <strong>Instructions:</strong> {instructionSnippet}
              </p>
            </div>
          );
        })}

        {/* Pagination Controls */}
        {results.length > 0 && (
          <div className="pagination-controls">
            <button
              className="pagination-btn"
              onClick={goToPrevPage}
              disabled={currentPage === 1}
            >
              Previous
            </button>
            <span className="pagination-info">
              Page {currentPage} of {totalPages}
            </span>
            <button
              className="pagination-btn"
              onClick={goToNextPage}
              disabled={currentPage === totalPages}
            >
              Next
            </button>
          </div>
        )}

        {/* If no results */}
        {results.length === 0 && (
          <p className="mt-4 text-gray-300">
            No results found. Try adjusting your search.
          </p>
        )}
      </div>
    </div>
  );
};

export default ResultsComponent;
