import { Menu, Transition } from '@headlessui/react';
import { ChevronDownIcon } from '@heroicons/react/20/solid';
import React, { Fragment, useState } from 'react';
import './SearchCard.css';

const SearchCard: React.FC = () => {
  const [ingredients, setIngredients] = useState<string[]>([]);
  const [searchType, setSearchType] = useState<string>('text');

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

  return (
    <div className="search-card">
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
            <Menu.Items className="dropdown-menu border border-gray-500 bg-gray-800 rounded-md mt-1">
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

      {searchType === 'ingredients' ? (
        <div>
          <label className="label">Add Ingredients</label>
          <input type="text" placeholder="Type an ingredient and press Enter" onKeyDown={addIngredient} className="input" />
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
        <div>
          <label className="label">Enter Your Search Text</label>
          <input type="text" placeholder="Type your search here..." className="input" />
        </div>
      )}

      <div className="mt-6">
        <button className="search-btn">Search Recipes</button>
      </div>
    </div>
  );
};

export default SearchCard;
