import { Menu, MenuItem } from '@headlessui/react';
import { GoogleIcon, MicrosoftIcon } from './icons';

const Header: React.FC = () => {
    return (
      <header className="bg-gray-900 bg-opacity-90 shadow-md text-white">
        <div className="container mx-auto flex justify-between items-center py-4 px-6">
          <h1 className="text-3xl font-semibold">Dishcovery</h1>
          <Menu as="div" className="relative">
            <Menu.Button className="text-sm font-medium focus:outline-none">
              Profile / Sign In
            </Menu.Button>
            <Menu.Items className="absolute right-0 mt-2 bg-white shadow-lg rounded-md py-1 w-48 text-gray-900">
              <MenuItem>
                {({ active }) => (
                  <button
                    className={`${
                      active ? 'bg-gray-100' : ''
                    } flex items-center px-4 py-2 w-full text-sm`}
                  >
                    <GoogleIcon className="mr-2 h-5 w-5" /> Sign in with Google
                  </button>
                )}
              </MenuItem>
              <MenuItem>
                {({ active }) => (
                  <button
                    className={`${
                      active ? 'bg-gray-100' : ''
                    } flex items-center px-4 py-2 w-full text-sm`}
                  >
                    <MicrosoftIcon className="mr-2 h-5 w-5" /> Sign in with Microsoft
                  </button>
                )}
              </MenuItem>
            </Menu.Items>
          </Menu>
        </div>
      </header>
    );
  };
  
  export default Header;