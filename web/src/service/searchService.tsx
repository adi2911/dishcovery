import axios from 'axios';
import { Recipe } from '../components/RecipeDetails';
import { CLOUD_RUN } from '../store/constants';

export interface SearchResponse {
  recipes: Recipe[];
  page: number;
  perPage: number;
  totalResults: number;
  totalPages: number;
  isError: boolean;
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
      url = `${CLOUD_RUN}/searchByText`;
      requestData = {
        text: searchText,
        exclude: exclusions,
        dietPreference,
      };
    }
    const response = await axios.post(url, requestData, {
      params: {
        page,
      },
      withCredentials: true,
    });

    const data = response.data;

    let recipeArray: Recipe[] = [];
    if (data.results) {
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
      isError:false
    };
  } catch (error) {
    console.log(">>>> catch is getting called")
    return {
      recipes: [],
      page: 0,
      perPage: 0,
      totalPages:0,
      totalResults:0,
      isError:true
    };
  }
}
