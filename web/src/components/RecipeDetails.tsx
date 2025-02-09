import axios from 'axios';
import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

interface Recipe {
  id: string;
  title: string;
  ingredients: string[];
  diet: string;
  instructions: string;
}

const RecipeDetail: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setError('No recipe ID provided');
      setLoading(false);
      return;
    }

    const fetchRecipe = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`http://127.0.0.1:5000/api/recipes/${id}`);
        setRecipe(response.data);
        setLoading(false);
      } catch (err: any) {
        setError('Recipe not found or an error occurred.');
        setLoading(false);
      }
    };

    fetchRecipe();
  }, [id]);

  // Return states: loading, error, or success
  if (loading) {
    return <div className="text-white">Loading...</div>;
  }

  if (error) {
    return (
      <div className="text-white">
        <p>{error}</p>
        <button onClick={() => navigate('/')}>Go back to search</button>
      </div>
    );
  }

  if (!recipe) {
    return (
      <div className="text-white">
        <p>No recipe found.</p>
        <button onClick={() => navigate('/')}>Go back to search</button>
      </div>
    );
  }

  return (
    <div className="text-white">
      <h1 className="text-3xl font-bold mb-4">{recipe.title}</h1>
      <p><strong>Diet:</strong> {recipe.diet}</p>
      <h2 className="text-xl font-semibold mt-4 mb-2">Ingredients</h2>
      <ul className="list-disc list-inside">
        {recipe.ingredients.map((ing, idx) => (
          <li key={idx}>{ing}</li>
        ))}
      </ul>
      <h2 className="text-xl font-semibold mt-4 mb-2">Instructions</h2>
      <p>{recipe.instructions}</p>

      <button
        className="mt-4 bg-gray-700 px-3 py-2 rounded"
        onClick={() => navigate('/')}
      >
        Back to Search
      </button>
    </div>
  );
};

export default RecipeDetail;
