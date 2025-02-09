import { Menu, Transition } from '@headlessui/react';
import { ChevronDownIcon } from '@heroicons/react/20/solid';
import axios from 'axios';
import React, { Fragment, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './SearchComponent.css';

// Example interface for recipe results
interface RecipeResult {
  id: string;                 // Unique ID for detail page
  title: string;
  ingredients: string[];
  diet: string;
  instructions: string;
}

const INITIAL_VIEW = 'initial'
const RESULT_VIEW = 'result'

const ITEMS_PER_PAGE = 10;

const SearchComponent: React.FC = () => {
  // -------------- Original SearchComponent States --------------
  const [ingredients, setIngredients] = useState<string[]>([]);
  const [exclusions, setExclusions] = useState<string[]>([]);
  const [searchType, setSearchType] = useState<string>('text');
  const [dietPreference, setDietPreference] = useState<string>('none');

  // **Add a state for the user's text input** (since we do search by text)
  const [searchText, setSearchText] = useState<string>('');

  // -------------- New States for Results Mode --------------
  const [results, setResults] = useState<RecipeResult[]>([]);
  const [currentPage, setCurrentPage] = useState<number>(1);

  const [viewMode, setViewMode] = useState(INITIAL_VIEW);

  const navigate = useNavigate();

  // ----------------- Original Handlers --------------------
  const addIngredient = (event: React.KeyboardEvent<HTMLInputElement>) => {
    const target = event.target as HTMLInputElement;
    if (event.key === 'Enter' && target.value.trim()) {
      setIngredients([...ingredients, target.value.trim()]);
      target.value = '';
    }
  };

  const removeIngredient = (index: number) => {
    setIngredients(ingredients.filter((_, i) => i !== index));
  };

  const addExclusion = (event: React.KeyboardEvent<HTMLInputElement>) => {
    const target = event.target as HTMLInputElement;
    if (event.key === 'Enter' && target.value.trim()) {
      setExclusions([...exclusions, target.value.trim()]);
      target.value = '';
    }
  };

  const removeExclusion = (index: number) => {
    setExclusions(exclusions.filter((_, i) => i !== index));
  };

  // ----------------- New: Handle Search --------------------
  const handleSearch = async () => {
    try {
      let response;
      // Decide which API to call
      if (searchType === 'ingredients') {
        response = await axios.post('http://127.0.0.1:5000/api/searchByIngredients', {
          ingredients,
          exclude: exclusions,
          dietPreference,
        });
      } else {
        // searchType === 'text'
        response = await axios.post('http://127.0.0.1:5000/api/searchByText', {
          text: searchText,
          exclude: exclusions,
          dietPreference,
        });
      }

      const data = response.data;
      if (data.results) {
        setResults(data.results);
      } else {
        setResults([]);
      }

      // Switch to "results" view
      setViewMode(RESULT_VIEW);
      setCurrentPage(1);
    } catch (error) {
      console.error('Search Error:', error);
      // Even if error, we might switch to results to show an empty list
      setResults([]);
      setViewMode(RESULT_VIEW);
    }
  };

  // ----------------- Pagination Logic --------------------
  const totalPages = Math.ceil(results.length / ITEMS_PER_PAGE);
  const currentStartIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const currentPageResults = results.slice(
    currentStartIndex,
    currentStartIndex + ITEMS_PER_PAGE
  );

  const goToNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage((prev) => prev + 1);
    }
  };

  const goToPrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage((prev) => prev - 1);
    }
  };

  // ----------------- Click on a Recipe Result --------------------
  const handleRecipeClick = (recipeId: string) => {
    // Navigate to detail page if you have a route like "/recipe/:id"
    navigate(`/recipe/${recipeId}`);
  };


  if (viewMode === INITIAL_VIEW) {
    // ============ ORIGINAL CARD UI ============

    return (
      <div className="search-card">
        <h2 className="title">Recipe Search</h2>

        {/* Search Type Dropdown */}
        <div className="mb-6">
          <label className="label">Search Type</label>
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
        <div className="mb-6">
          <label className="label">Diet Preference</label>
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

        {/* Conditional: Ingredients or Text */}
        {searchType === 'ingredients' ? (
          <div className="mb-6">
            <label className="label">Add Ingredients</label>
            <input
              type="text"
              placeholder="Type an ingredient and press Enter"
              onKeyDown={addIngredient}
              className="input"
            />
            <div className="ingredients-container">
              {ingredients.map((ingredient, index) => (
                <div key={index} className="ingredient-item">
                  {ingredient}
                  <button onClick={() => removeIngredient(index)} className="close-btn">
                    ✖
                  </button>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="mb-6">
            <label className="label">Enter Your Search Text</label>
            <input
              type="text"
              placeholder="Type your search here..."
              className="input"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
          </div>
        )}

        {/* Exclusions */}
        <div className="mb-6">
          <label className="label">Exclude These</label>
          <input
            type="text"
            placeholder="Type exclusions and press Enter"
            onKeyDown={addExclusion}
            className="input"
          />
          <div className="ingredients-container">
            {exclusions.map((ex, index) => (
              <div key={index} className="ingredient-item">
                {ex}
                <button onClick={() => removeExclusion(index)} className="close-btn">
                  ✖
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Search Button */}
        <div className="mt-6">
          <button className="search-btn" onClick={handleSearch}>
            Search Recipes
          </button>
        </div>
      </div>
    );
  } else {
    // ============ RESULTS MODE ============

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
                onKeyDown={(e) => addIngredient(e)}
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
              onKeyDown={(e) => addExclusion(e)}
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
            const snippet = recipe.instructions.slice(0, 80) +
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
  }
};

export default SearchComponent;
