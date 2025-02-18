// SearchComponent.tsx
import { Menu, Transition } from '@headlessui/react';
import { ChevronDownIcon } from '@heroicons/react/20/solid';
import React, { Fragment, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { performSearch } from '../service/searchService';
import ResultsComponent from './ResultsComponent';
import './SearchComponent.css';

// Import the new autocomplete input
import AutoComplete from './AutoComplete';
import { Recipe } from './RecipeDetails';

const INITIAL_VIEW = 'initial';
const RESULT_VIEW = 'result';
const ITEMS_PER_PAGE = 10;

const SearchComponent: React.FC = () => {
  // ------------------------------ States ------------------------------
  const [ingredients, setIngredients] = useState<string[]>([]);
  const [exclusions, setExclusions] = useState<string[]>([]);
  const [searchType, setSearchType] = useState<string>('text');
  const [dietPreference, setDietPreference] = useState<string>('none');

  // For text-based searching
  const [searchText, setSearchText] = useState<string>('');

  // For results
  const [results, setResults] = useState<Recipe[]>([]);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [viewMode, setViewMode] = useState(INITIAL_VIEW);

  const navigate = useNavigate();

  // ------------------------- Ingredient Handlers -------------------------
  // Original "Enter" key handler
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

  // NEW: Handler for adding an ingredient from the Autocomplete component
  const handleAddIngredientFromAutocomplete = (ingredient: string) => {
    setIngredients((prev) => [...prev, ingredient]);
  };

  // ------------------------- Exclusion Handlers -------------------------
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

  // -------------------------- Main Search Handler -----------------------
  const handleSearch = async () => {
    const data  = await performSearch(
      searchType,
      ingredients,
      exclusions,
      dietPreference,
      searchText
    );
    console.log("data",data)
    setResults(data);
    setViewMode(RESULT_VIEW);
    setCurrentPage(1);
  };

  // ------------------------- Pagination Logic ---------------------------
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

  // ---------------------- Navigate to Recipe Detail ----------------------
  const handleRecipeClick = (recipeId: string) => {
    navigate(`/recipe/${recipeId}`);
  };

  // --------------------- Conditional Rendering Logic ---------------------
  if (viewMode === INITIAL_VIEW) {
    return (
      <div className="search-card">
        <h2 className="title">Recipe Search</h2>

        {/* ============== Search Type Dropdown ============== */}
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

        {/* ============== Diet Preference Dropdown ============== */}
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

        {/* ============== Conditional Rendering: Text vs. Ingredients ============== */}
        {searchType === 'ingredients' ? (
          <div className="mb-6">
            <label className="label">Add Ingredients</label>

            {/* Autocomplete Input for Ingredients */}
            <AutoComplete onAddIngredient={handleAddIngredientFromAutocomplete} />

            {/* Uncomment if you want to keep the old manual input 
            <input
              type="text"
              placeholder="Type an ingredient and press Enter"
              onKeyDown={addIngredient}
              className="input"
            />
            */}
            
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

        {/* ============== Exclusions ============== */}
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

        {/* ============== Search Button ============== */}
        <div className="mt-6">
          <button className="search-btn" onClick={handleSearch}>
            Search Recipes
          </button>
        </div>
      </div>
    );
  } else {
    // ================== Results View ==================
    return (
      <ResultsComponent
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
        handleSearch={handleSearch}
        results={results}
        currentPage={currentPage}
        totalPages={totalPages}
        goToNextPage={goToNextPage}
        goToPrevPage={goToPrevPage}
        currentPageResults={currentPageResults}
        handleRecipeClick={handleRecipeClick}
      />
    );
  }
};

export default SearchComponent;
