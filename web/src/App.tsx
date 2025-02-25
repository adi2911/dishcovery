import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./App.css";
import Header from "./components/Header";
import RecipeDetail from "./components/RecipeDetails";
import SearchComponent from "./components/SearchComponent";
import { SearchProvider } from "./store/SearchContext";
import { UserProvider } from "./store/UserContext";

export default function App() {
  return (
    <BrowserRouter>
      <UserProvider>
        <SearchProvider>
          <div
            className="min-h-screen bg-cover bg-center"
            style={{
              backgroundImage:
                "url('https://images.unsplash.com/photo-1504674900247-0877df9cc836?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080')",
            }}
          >
            <Header />
            <div className="container mx-auto py-10 px-6">
              <Routes>
                <Route path="/" element={<SearchComponent />} />
                <Route path="/recipe/:id" element={<RecipeDetail />} />
              </Routes>
            </div>
          </div>
        </SearchProvider>
      </UserProvider>
    </BrowserRouter>
  );
}
