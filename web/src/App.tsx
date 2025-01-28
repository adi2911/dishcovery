import "./App.css";
import Header from './components/Header';
import SearchCard from './components/SearchCard';

export default function App() {
  return (
    <div
      className="min-h-screen bg-cover bg-center"
      style={{
        backgroundImage:
          "url('https://images.unsplash.com/photo-1504674900247-0877df9cc836?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080')",
      }}
    >
      <Header />
      <div className="container mx-auto py-10 px-6">
        <SearchCard />
      </div>
    </div>
  );
}
