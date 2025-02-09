import { GoogleOAuthProvider } from '@react-oauth/google';
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
   <GoogleOAuthProvider clientId="230003814546-0eg898eeo02cihjlrubkvqjl0qt9tjbo.apps.googleusercontent.com">
    <App />
  </GoogleOAuthProvider>,
  </React.StrictMode>
);

