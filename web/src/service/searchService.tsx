// searchService.ts
import axios from 'axios';
import { Recipe } from '../components/RecipeDetails'; // We'll import the interface from SearchComponent

export async function performSearch(
  searchType: string,
  ingredients: string[],
  exclusions: string[],
  dietPreference: string,
  searchText: string
): Promise<Recipe[]> {
  try {
    let response;
    if (searchType === 'ingredients') {
      response = await axios.post('http://127.0.0.1:5000/api/searchByIngredients', {
        ingredients,
        exclude: exclusions,
        dietPreference,
      });
    } else {
      // searchType === 'text'
      response = await axios.post('http://127.0.0.1:5000/api/searchByText', {
        text: searchText,
        exclude: exclusions,
        dietPreference,
      });
    }

    const data = response.data;
    if (data.results) {
      const recipeArray: Recipe[] = Object.entries(data.results).map(([key, value]) => {
        const recipe = value as Omit<Recipe, "id">;
        return ({
        id: key,
        title: recipe?.title ?? "",
        ingredients: recipe?.ingredients ?? [],
        diet: recipe?.diet ?? "",
        instructions: recipe?.instructions ?? [],
        url : recipe?.url ?? ''
      })});
      return recipeArray;
    }
    return [];
  } catch (error) {
    console.error('Search Error:', error);
    // Return an empty array on error, same as your original logic
    return [];
  }
}
