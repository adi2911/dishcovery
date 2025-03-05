import { useNavigate } from 'react-router-dom';
import { useSearch } from '../store/SearchContext';

const Header = () => {
  const navigate = useNavigate();
  const { setSearchState } = useSearch();

  const handleLogoClick = () => {
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
      error: false,
    }));
    navigate('/');
  };

  return (
    <header className="bg-gray-900 bg-opacity-90 shadow-md text-white">
      <div className="container mx-auto flex justify-between items-center py-4 px-6">
        <h1
          className="text-3xl font-semibold cursor-pointer"
          onClick={handleLogoClick}
        >
          Dishcovery
        </h1>
      </div>
    </header>
  );
};

export default Header;
