// searchService.ts
import axios from 'axios';
import { Recipe } from '../components/RecipeDetails';
import { CLOUD_RUN } from '../store/constants';

export interface SearchResponse {
  recipes: Recipe[];
  page: number;
  perPage: number;
  totalResults: number;
  totalPages: number;
}

export async function performSearch(
  searchType: string,
  ingredients: string[],
  exclusions: string[],
  dietPreference: string,
  searchText: string,
  page: number = 1
): Promise<SearchResponse> {
  try {
    let url = '';
    let requestData: any = {};

    if (searchType === 'ingredients') {
      url = `${CLOUD_RUN}/searchByIngredients`;
      requestData = {
        ingredients,
        exclude: exclusions,
        dietPreference,
      };
    } else {
      // searchType === 'text'
      url = `${CLOUD_RUN}/searchByText`;
      requestData = {
        text: searchText,
        exclude: exclusions,
        dietPreference,
      };
    }

    /**
     *  For Axios POST, the syntax is:
     *    axios.post(url, data, config)
     *
     *  We move `page` into config.params instead of body.
     */
    const response = await axios.post(url, requestData, {
      params: {
        page,   // <--- send page as a query parameter
      },
    });

    const data = response.data;

    // Convert "results" field into a Recipe[] as before
    let recipeArray: Recipe[] = [];
    if (data.results) {
      // data.results is already an array of { id, title, ingredients, ... }
      recipeArray = data.results.map((r: any) => {
        return {
          id: r.id,
          title: r.title ?? '',
          ingredients: r.ingredients ?? [],
          diet: r.diet ?? '',
          instructions: r.instructions ?? '',
          url: r.url ?? ''
        };
      });
    }

    // Extract pagination info from the response
    const pageFromServer = data.page ?? 1;
    const perPage = data.per_page ?? 10;
    const totalResults = data.total_results ?? recipeArray.length;
    const totalPages = data.total_pages ?? 1;

    return {
      recipes: recipeArray,
      page: pageFromServer,
      perPage,
      totalResults,
      totalPages,
    };
  } catch (error) {
    console.error('Search Error:', error);
    return {
      recipes: [],
      page: 1,
      perPage: 10,
      totalResults: 0,
      totalPages: 1,
    };
  }
}
