// AutoComplete.tsx
import axios from 'axios';
import React, { useEffect, useRef, useState } from 'react';

interface AutoCompleteProps {
  onAddIngredient: (ingredient: string) => void;
}

const AutoComplete: React.FC<AutoCompleteProps> = ({ onAddIngredient }) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);

  // For debouncing the API calls
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  // Track which suggestion is currently "active" (highlighted)
  const [activeSuggestionIndex, setActiveSuggestionIndex] = useState<number>(-1);

  // ============================ Fetching Suggestions ============================
  const fetchSuggestions = async (searchTerm: string) => {
    if (searchTerm.length < 2) {
      setSuggestions([]);
      setActiveSuggestionIndex(-1);
      return;
    }

    // 1) Check localStorage cache first
    const cacheKey = `auto_${searchTerm.toLowerCase()}`;
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      const cachedData = JSON.parse(cached) as string[];
      setSuggestions(cachedData);
      setActiveSuggestionIndex(-1);
      return;
    }

    // 2) If not cached, make request
    try {
      setLoading(true);
      const response = await axios.get(
        `http://127.0.0.1:5000/api/autocomplete?query=${encodeURIComponent(searchTerm)}`
      );
      const data = response.data as string[];
      setSuggestions(data);
      setActiveSuggestionIndex(-1);

      // 3) Cache in localStorage for next time
      localStorage.setItem(cacheKey, JSON.stringify(data));
    } catch (err) {
      console.error('Autocomplete Error:', err);
      setSuggestions([]);
      setActiveSuggestionIndex(-1);
    } finally {
      setLoading(false);
    }
  };

  // Debounce effect
  useEffect(() => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }
    debounceTimer.current = setTimeout(() => {
      if (query.trim().length >= 2) {
        fetchSuggestions(query.trim());
      } else {
        setSuggestions([]);
        setActiveSuggestionIndex(-1);
      }
    }, 200);

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [query]);

  // ============================ Handle Key Down ============================
  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    // If no suggestions, do nothing special
    if (!suggestions.length) return;

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        // Move down the list (activeSuggestionIndex + 1)
        setActiveSuggestionIndex((prevIndex) => {
          const nextIndex = prevIndex + 1;
          return nextIndex >= suggestions.length ? 0 : nextIndex;
        });
        break;

      case 'ArrowUp':
        event.preventDefault();
        // Move up the list (activeSuggestionIndex - 1)
        setActiveSuggestionIndex((prevIndex) => {
          const nextIndex = prevIndex - 1;
          return nextIndex < 0 ? suggestions.length - 1 : nextIndex;
        });
        break;

      case 'Enter':
        event.preventDefault();
        // If we have a valid active index, pick that item
        if (activeSuggestionIndex >= 0 && activeSuggestionIndex < suggestions.length) {
          onAddIngredient(suggestions[activeSuggestionIndex]);
        } else {
          // If no valid active index, but we do have suggestions, pick the first
          onAddIngredient(suggestions[0]);
        }
        // Clear everything
        setQuery('');
        setShowSuggestions(false);
        setSuggestions([]);
        setActiveSuggestionIndex(-1);
        break;

      default:
        break;
    }
  };

  // ============================ Handle Input Change ============================
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    setShowSuggestions(true);
    setActiveSuggestionIndex(-1);
  };

  // ============================ Click on a suggestion ============================
  const handleSuggestionClick = (suggestion: string, index: number) => {
    onAddIngredient(suggestion);
    setQuery('');
    setShowSuggestions(false);
    setSuggestions([]);
    setActiveSuggestionIndex(-1);
  };

  // ============================ Render ============================
  return (
    <div style={{ position: 'relative' }}>
      <input
        type="text"
        placeholder="Type an ingredient and press Enter"
        className="input"
        value={query}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
      />
      {loading && <div className="loading-spinner">Loading...</div>}

      {showSuggestions && suggestions.length > 0 && (
        <ul className="suggestions-dropdown">
          {suggestions.map((item, index) => {
            const isActive = index === activeSuggestionIndex;
            return (
              <li
                key={index}
                onClick={() => handleSuggestionClick(item, index)}
                className={`suggestion-item ${isActive ? 'active-suggestion' : ''}`}
              >
                {item}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
};

export default AutoComplete;
