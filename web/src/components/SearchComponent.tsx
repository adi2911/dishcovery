import { Menu, Transition } from '@headlessui/react';
import { ChevronDownIcon } from '@heroicons/react/20/solid';
import React, { Fragment, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { performSearch, SearchResponse } from '../service/searchService';
import { useSearch } from '../store/SearchContext';
import AutoComplete from './AutoComplete';
import { Recipe } from './RecipeDetails';
import ResultsComponent from './ResultsComponent';

const SearchComponent: React.FC = () => {
  const navigate = useNavigate();

  // Pull searchState + setSearchState from your custom context
  const { searchState, setSearchState } = useSearch();
  const [timeTaken, setTimeTaken] = useState(0);
  const {
    results,
    currentPage,
    totalPages,
    searchType,
    dietPreference,
    ingredients,
    exclusions,
    searchText,
  } = searchState;

  // Provide local callbacks that match (value: string) => void usage
  const setSearchType = (newVal: string) =>
    setSearchState((prev) => ({ ...prev, searchType: newVal }));
  const setDietPreference = (newVal: string) =>
    setSearchState((prev) => ({ ...prev, dietPreference: newVal }));
  const setSearchText = (newVal: string) =>
    setSearchState((prev) => ({ ...prev, searchText: newVal }));

  // For arrays
  const setIngredients = (ings: string[]) =>
    setSearchState((prev) => ({ ...prev, ingredients: ings }));
  const setExclusions = (ex: string[]) =>
    setSearchState((prev) => ({ ...prev, exclusions: ex }));

  const setResults = (recipes: Recipe[]) =>
    setSearchState((prev) => ({ ...prev, results: recipes }));
  const setCurrentPage = (page: number) =>
    setSearchState((prev) => ({ ...prev, currentPage: page }));
  const setTotalPages = (tp: number) =>
    setSearchState((prev) => ({ ...prev, totalPages: tp }));

  // Handlers for adding/removing ingredients
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

  // Handlers for exclusions
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

  const handleAddIngredientFromAutocomplete = (ingredient: string) => {
    setIngredients([...ingredients, ingredient]);
  };


  function startTimer(): number {
    return performance.now();
  }
  
  function endTimer(startTime: number): number {
    const endTime = performance.now();
    const duration = endTime - startTime; // duration in milliseconds
    return duration;
  }
  // Main search function
  const handleSearch = async (page = 1) => {

    const startTime = startTimer();
    
    const data: SearchResponse = await performSearch(
      searchType,
      ingredients,
      exclusions,
      dietPreference,
      searchText,
      page
    );
    setResults(data.recipes);
    setCurrentPage(data.page);
    setTotalPages(data.totalPages);

    const endTime = endTimer(startTime);
    setTimeTaken(endTime)
  };

  // Specifically triggers a “fresh” search at page=1
  const handleInitialSearch = () => {
    handleSearch(1);
  };

  // Pagination
  const goToNextPage = async () => {
    if (currentPage < totalPages) {
      await handleSearch(currentPage + 1);
    }
  };
  const goToPrevPage = async () => {
    if (currentPage > 1) {
      await handleSearch(currentPage - 1);
    }
  };

  // Clicking a recipe
  const handleRecipeClick = (recipeId: string) => {
    navigate(`/recipe/${recipeId}`);
  };

  // Decide whether to show initial or results view
  const hasSearched = results.length > 0;

  if (!hasSearched) {
    // -- INITIAL VIEW --
    return (
      <div
        className="search-card"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            const activeEl = document.activeElement as HTMLInputElement | null;
            if (!activeEl) {
              handleInitialSearch();
              return;
            }

            const nameAttr = activeEl.getAttribute('name');
            if (
              nameAttr === 'ingredientInput' ||
              nameAttr === 'exclusionInput'
            ) {
              // If there's typed text, let the input's own onKeyDown handle it => do nothing here
              // If empty, trigger the search
              if (!activeEl.value.trim()) {
                handleInitialSearch();
              }
            } else {
              // Not an ingredient or exclusion field => do the search
              handleInitialSearch();
            }
          }
        }}
      >
        <h2 className="title">Recipe Search</h2>

        {/* -- Search Type Dropdown -- */}
        <div className="mb-6">
          <label className="label">Search Type</label>
          <Menu as="div" className="relative inline-block w-full">
            <div>
              <Menu.Button className="dropdown-button">
                {searchType === 'text'
                  ? 'Search by Text'
                  : 'Search by Ingredients'}
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

        {/* -- Diet Preference Dropdown -- */}
        <div className="mb-6">
          <label className="label">Diet Preference</label>
          <Menu as="div" className="relative inline-block w-full">
            <div>
              <Menu.Button className="dropdown-button">
                {dietPreference === 'none'
                  ? 'No Preference'
                  : dietPreference.charAt(0).toUpperCase() +
                    dietPreference.slice(1)}
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

        {/* -- Conditional Rendering: Text vs Ingredients -- */}
        {searchType === 'ingredients' ? (
          <div className="mb-6">
            <label className="label">Add Ingredients</label>

            <AutoComplete onAddIngredient={handleAddIngredientFromAutocomplete} />

            <div className="ingredients-container">
              {ingredients.map((ingredient, index) => (
                <div key={index} className="ingredient-item">
                  {ingredient}
                  <button
                    onClick={() => removeIngredient(index)}
                    className="close-btn"
                  >
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

        {/* -- Exclusions -- */}
        <div className="mb-6">
          <label className="label">Exclude These</label>
          <input
            type="text"
            name="exclusionInput"
            placeholder="Type exclusions and press Enter"
            onKeyDown={addExclusion}
            className="input"
          />
          <div className="ingredients-container">
            {exclusions.map((ex, index) => (
              <div key={index} className="ingredient-item">
                {ex}
                <button
                  onClick={() => removeExclusion(index)}
                  className="close-btn"
                >
                  ✖
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* -- Search Button -- */}
        <div className="mt-6">
          <button className="search-btn" onClick={handleInitialSearch}>
            Search Recipes
          </button>
        </div>
      </div>
    );
  } else {
    // ------------------ RESULTS VIEW ------------------
    return (
      <ResultsComponent
        timeTaken = {timeTaken}
        searchType={searchType}
        setSearchType={setSearchType}
        dietPreference={dietPreference}
        setDietPreference={setDietPreference}
        ingredients={ingredients}
        addIngredient={addIngredient}
        removeIngredient={removeIngredient}
        exclusions={exclusions}
        addExclusion={addExclusion}
        removeExclusion={removeExclusion}
        searchText={searchText}
        setSearchText={setSearchText}
        handleSearch={() => handleSearch(1)}
        results={results}
        currentPage={currentPage}
        totalPages={totalPages}
        goToNextPage={goToNextPage}
        goToPrevPage={goToPrevPage}
        currentPageResults={results}
        handleRecipeClick={handleRecipeClick}
      />
    );
  }
};

export default SearchComponent;
