// ResultsComponent.tsx
import { Menu } from '@headlessui/react';
import React from 'react';
import { Recipe } from './RecipeDetails';
import './SearchComponent.css';

interface ResultsComponentProps {
  searchType: string;
  setSearchType: React.Dispatch<React.SetStateAction<string>>;
  dietPreference: string;
  setDietPreference: React.Dispatch<React.SetStateAction<string>>;

  ingredients: string[];
  addIngredient: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  removeIngredient: (index: number) => void;

  exclusions: string[];
  addExclusion: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  removeExclusion: (index: number) => void;

  searchText: string;
  setSearchText: React.Dispatch<React.SetStateAction<string>>;

  handleSearch: () => void;

  results: Recipe[];        // entire page of results from the server
  currentPage: number;
  totalPages: number;
  goToNextPage: () => void;
  goToPrevPage: () => void;

  currentPageResults: Recipe[];
  handleRecipeClick: (recipeId: string) => void;
}

const ResultsComponent: React.FC<ResultsComponentProps> = ({
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
  return (
    <div className="results-mode-container text-white p-4">
      {/* -- Top row: same as before, allowing user to refine and re-search -- */}
      <div className="top-filters flex flex-wrap items-end gap-4 mb-6">
        {/* Search Type Dropdown */}
        <div className="filter-item">
          <label className="filter-label">Search Type</label>
          <Menu as="div" className="relative inline-block w-full">
            {/* ...same as before... */}
          </Menu>
        </div>

        {/* Diet Preference Dropdown */}
        <div className="filter-item">
          <label className="filter-label">Diet Preference</label>
          <Menu as="div" className="relative inline-block w-full">
            {/* ...same as before... */}
          </Menu>
        </div>

        {/* Conditional: Ingredients vs Text */}
        {searchType === 'ingredients' ? (
          <div className="filter-item">
            <label className="filter-label">Ingredients</label>
            <input
              type="text"
              placeholder="Enter ingredient, press Enter"
              className="filter-input"
              onKeyDown={addIngredient}
            />
          </div>
        ) : (
          <div className="filter-item">
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
        <div className="filter-item">
          <label className="filter-label">Exclusions</label>
          <input
            type="text"
            placeholder="Exclude items, press Enter"
            className="filter-input"
            onKeyDown={addExclusion}
          />
        </div>

        {/* Re-Search button */}
        <div className="filter-item">
          <button className="search-btn" onClick={handleSearch}>
            Search
          </button>
        </div>
      </div>

      {/* Show chips for Ingredients + Exclusions (same as before) */}
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
            recipe.ingredients.length > 3 ? ingredientHighlights + '...' : ingredientHighlights;

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
