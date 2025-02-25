import axios from 'axios';
import React, { useEffect, useRef, useState } from 'react';
import { CLOUD_RUN } from '../store/constants';

interface AutoCompleteProps {
  onAddIngredient: (ingredient: string) => void;
}

const AutoComplete: React.FC<AutoCompleteProps> = ({ onAddIngredient }) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeSuggestionIndex, setActiveSuggestionIndex] = useState<number>(-1);
  const suggestionListRef = useRef<HTMLUListElement | null>(null);

  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  const fetchSuggestions = async (searchTerm: string) => {
    if (searchTerm.length < 2) {
      setSuggestions([]);
      setActiveSuggestionIndex(-1);
      return;
    }

    const cacheKey = `auto_${searchTerm.toLowerCase()}`;
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      const cachedData = JSON.parse(cached) as string[];
      setSuggestions(cachedData);
      setActiveSuggestionIndex(-1);
      return;
    }

    try {
      setLoading(true);
      const response = await axios.get(
        `${CLOUD_RUN}/autocomplete?query=${encodeURIComponent(searchTerm)}`
      );
      const data = response.data as string[];
      setSuggestions(data);
      setActiveSuggestionIndex(-1);
      localStorage.setItem(cacheKey, JSON.stringify(data));
    } catch (err) {
      console.error('Autocomplete Error:', err);
      setSuggestions([]);
      setActiveSuggestionIndex(-1);
    } finally {
      setLoading(false);
    }
  };

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

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (!suggestions.length) return;

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        setActiveSuggestionIndex((prevIndex) => {
          const nextIndex = prevIndex + 1;
          return nextIndex >= suggestions.length ? 0 : nextIndex;
        });
        break;

      case 'ArrowUp':
        event.preventDefault();
        setActiveSuggestionIndex((prevIndex) => {
          const nextIndex = prevIndex - 1;
          return nextIndex < 0 ? suggestions.length - 1 : nextIndex;
        });
        break;

      case 'Enter':
        event.preventDefault();
        if (activeSuggestionIndex >= 0 && activeSuggestionIndex < suggestions.length) {
          onAddIngredient(suggestions[activeSuggestionIndex]);
        } else if (suggestions.length > 0) {
          onAddIngredient(suggestions[0]);
        }
        setQuery('');
        setShowSuggestions(false);
        setSuggestions([]);
        setActiveSuggestionIndex(-1);
        break;

      default:
        break;
    }
  };

  useEffect(() => {
    if (suggestionListRef.current && activeSuggestionIndex >= 0) {
      const activeItem = suggestionListRef.current.children[activeSuggestionIndex] as HTMLElement;
      if (activeItem) {
        activeItem.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    }
  }, [activeSuggestionIndex]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    setShowSuggestions(true);
    setActiveSuggestionIndex(-1);
  };

  const handleSuggestionClick = (suggestion: string) => {
    onAddIngredient(suggestion);
    setQuery('');
    setShowSuggestions(false);
    setSuggestions([]);
    setActiveSuggestionIndex(-1);
  };

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
        <ul className="suggestions-dropdown" ref={suggestionListRef}>
          {suggestions.map((item, index) => (
            <li
              key={index}
              onClick={() => handleSuggestionClick(item)}
              className={`suggestion-item ${index === activeSuggestionIndex ? 'active-suggestion' : ''}`}
            >
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default AutoComplete;
