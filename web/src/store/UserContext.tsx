import { googleLogout, useGoogleLogin } from '@react-oauth/google';
import axios from 'axios';
import { createContext, ReactNode, useContext, useEffect, useState } from 'react';


interface User {
  name: string;
  email: string;
  user_id: string;
  preferences?: string[];
}

interface UserContextType {
  user: User | null;
  setUser: (user: User | null) => void;
  signOut: () => void;
  signIn:() => void;
  fetchCurrentUser: () => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);

  const fetchCurrentUser = async () => {
    try {
      const res = await axios.get('https://backend-service-230003814546.europe-west2.run.app/api/user', { withCredentials: true });
      setUser(res.data.user);
    } catch (error) {
      console.log('No active session');
    }
  };

  const signOut = async () => {
    try {
      await axios.post('https://backend-service-230003814546.europe-west2.run.app/api/signout', {}, { withCredentials: true });
      setUser(null);
      console.log('User signed out successfully');
      googleLogout();
    } catch (error) {
      console.error('Sign-out error:', error);
    }
  };

  const signIn =  useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        const res = await axios.post('https://backend-service-230003814546.europe-west2.run.app/api/signin', {
          token: tokenResponse.access_token,
        }, { withCredentials: true });

        console.log('User signed in:', res.data.user);
        setUser(res.data.user);
      } catch (error) {
        console.error('Sign-in error:', error);
      }
    },
    onError: () => console.log('Login Failed'),
    flow: "implicit",
    scope: "openid email profile"
  });
  

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  return (
    <UserContext.Provider value={{ user, setUser, signOut, signIn, fetchCurrentUser }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};
