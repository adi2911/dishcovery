import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react';
import { useNavigate } from 'react-router-dom';
import { useSearch } from '../store/SearchContext'; // <-- ADDED
import { useUser } from '../store/UserContext';
import { GoogleIcon } from './icons';

const Header = () => {
  const navigate = useNavigate();
  const { user, signIn, signOut } = useUser();
  const { setSearchState } = useSearch(); // <-- ADDED

  const googleLogin = async () => {
    await signIn();
  };

  const handleSignOut = async () => {
    await signOut();
  };

  // NEW: Clear search state and navigate to initial view
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
    }));
    navigate('/');
  };

  return (
    <header className="bg-gray-900 bg-opacity-90 shadow-md text-white">
      <div className="container mx-auto flex justify-between items-center py-4 px-6">
        {/* UPDATED onClick to call handleLogoClick */}
        <h1
          className="text-3xl font-semibold cursor-pointer"
          onClick={handleLogoClick}
        >
          Dishcovery
        </h1>
        <Menu as="div" className="relative">
          <MenuButton className="text-sm font-medium focus:outline-none">
            {user ? user.name : 'Profile / Sign In'}
          </MenuButton>
          <MenuItems className="absolute right-0 mt-2 bg-white shadow-lg rounded-md py-1 w-48 text-gray-900">
            {!user ? (
              <MenuItem>
                {({ active }) => (
                  <button
                    className={`${active ? 'bg-gray-100' : ''} flex items-center px-4 py-2 w-full text-sm`}
                    onClick={() => googleLogin()}
                  >
                    <GoogleIcon className="mr-2 h-5 w-5" /> Sign in with Google
                  </button>
                )}
              </MenuItem>
            ) : (
              <MenuItem>
                {({ active }) => (
                  <button
                    className={`${active ? 'bg-gray-100' : ''} flex items-center px-4 py-2 w-full text-sm`}
                    onClick={handleSignOut}
                  >
                    Sign Out
                  </button>
                )}
              </MenuItem>
            )}
          </MenuItems>
        </Menu>
      </div>
    </header>
  );
};

export default Header;
