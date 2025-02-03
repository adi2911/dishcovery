import { Menu, Transition } from '@headlessui/react';
import { ChevronDownIcon } from '@heroicons/react/20/solid';
import React, { Fragment, useState } from 'react';
import './SearchCard.css';

const SearchCard: React.FC = () => {
  const [ingredients, setIngredients] = useState<string[]>([]);
  const [exclusions, setExclusions] = useState<string[]>([]);
  const [searchType, setSearchType] = useState<string>('text');
  const [dietPreference, setDietPreference] = useState<string>('none');

  // Handle "Add Ingredients"
  const addIngredient = (event: React.KeyboardEvent<HTMLInputElement>) => {
    const target = event.target as HTMLInputElement;
    if (event.key === 'Enter' && target.value.trim()) {
      setIngredients([...ingredients, target.value.trim()]);
      target.value = '';
    }
  };

  // Handle "Remove Ingredient"
  const removeIngredient = (index: number) => {
    setIngredients(ingredients.filter((_, i) => i !== index));
  };

  // Handle "Add Exclusion"
  const addExclusion = (event: React.KeyboardEvent<HTMLInputElement>) => {
    const target = event.target as HTMLInputElement;
    if (event.key === 'Enter' && target.value.trim()) {
      setExclusions([...exclusions, target.value.trim()]);
      target.value = '';
    }
  };

  // Handle "Remove Exclusion"
  const removeExclusion = (index: number) => {
    setExclusions(exclusions.filter((_, i) => i !== index));
  };

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
              {dietPreference === 'none' ? 'No Preference' : dietPreference.charAt(0).toUpperCase() + dietPreference.slice(1)}
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
                <button onClick={() => removeIngredient(index)} className="close-btn">✖</button>
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
              <button onClick={() => removeExclusion(index)} className="close-btn">✖</button>
            </div>
          ))}
        </div>
      </div>

      {/* Search Button */}
      <div className="mt-6">
        <button className="search-btn">Search Recipes</button>
      </div>
    </div>
  );
};

export default SearchCard;
