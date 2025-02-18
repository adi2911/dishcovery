import { Menu, Transition } from '@headlessui/react';
import { ChevronDownIcon } from '@heroicons/react/20/solid';
import React, { Fragment } from 'react';
import { Recipe } from './RecipeDetails'; // Use the same interface
import './SearchComponent.css'; // Re-use your same styling

interface ResultsComponentProps {
  // All states/handlers that you used in "results" mode
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

  results: Recipe[];
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
      {/* Top row filters so user can refine search again */}
      <div className="top-filters flex flex-wrap items-end gap-4 mb-6">
        {/* Search Type Dropdown */}
        <div className="filter-item">
          <label className="filter-label">Search Type</label>
          <Menu as="div" className="relative inline-block w-full">
            <div>
              <Menu.Button className="dropdown-button">
                {searchType === 'text' ? 'Search by Text' : 'Search by Ingredients'}
                <ChevronDownIcon className="w-5 h-5 ml-2 inline" />
              </Menu.Button>
            </div>
            <Transition
              as={Fragment}
              enter="transition ease-out duration-100"
              enterFrom="transform opacity-0 scale-95"
              enterTo="transform opacity-100 scale-100"
              leave="transition ease-in duration-75"
              leaveFrom="transform opacity-100 scale-100"
              leaveTo="transform opacity-0 scale-95"
            >
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
            </Transition>
          </Menu>
        </div>

        {/* Diet Preference Dropdown */}
        <div className="filter-item">
          <label className="filter-label">Diet Preference</label>
          <Menu as="div" className="relative inline-block w-full">
            <div>
              <Menu.Button className="dropdown-button">
                {dietPreference === 'none'
                  ? 'No Preference'
                  : dietPreference.charAt(0).toUpperCase() + dietPreference.slice(1)}
                <ChevronDownIcon className="w-5 h-5 ml-2 inline" />
              </Menu.Button>
            </div>
            <Transition
              as={Fragment}
              enter="transition ease-out duration-100"
              enterFrom="transform opacity-0 scale-95"
              enterTo="transform opacity-100 scale-100"
              leave="transition ease-in duration-75"
              leaveFrom="transform opacity-100 scale-100"
              leaveTo="transform opacity-0 scale-95"
            >
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
            </Transition>
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

      {/* Show Chips for current ingredients/exclusions */}
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

      {/* Results List + Pagination */}
      <div className="results-container mt-6">
        {currentPageResults.map((recipe) => {
          // Truncate instructions for preview
          const snippet =
            recipe.instructions.slice(0, 80) +
            (recipe.instructions.length > 80 ? '...' : '');
          // Show first 3 ingredients
          const ingredientHighlights = recipe.ingredients.slice(0, 3).join(', ');

          return (
            <div
              key={recipe.id}
              className="result-item"
              onClick={() => handleRecipeClick(recipe.id)}
            >
              <h3 className="result-title">{recipe.title}</h3>
              <p className="result-subtitle">
                <strong>Ingredients:</strong> {ingredientHighlights}
                {recipe.ingredients.length > 3 ? '...' : ''}
              </p>
              <p className="result-snippet">
                <strong>Instructions:</strong> {snippet}
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

        {/* If no results, show a small note */}
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
