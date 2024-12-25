import React, { useState } from "react";
import { useTags } from './index.js'
import api from '../api'

export default function useRecipes () {
  const [ recipes, setRecipes ] = useState([])
  const [ recipesCount, setRecipesCount ] = useState(0)
  const [ recipesPage, setRecipesPage ] = useState(1)
  const { value: tagsValue, handleChange: handleTagsChange, setValue: setTagsValue } = useTags()

  const handleLike = ({ id, toLike }) => {
    // Select the appropriate API method based on the action
    const method = toLike
      ? api.addToFavorites.bind(api)
      : api.removeFromFavorites.bind(api);
  
    method({ id })
      .then((res) => {
        // Ensure the response is valid (optional validation step)
        if (!res) {
          console.log(res);
          throw new Error("Unexpected response from the API");
        }
  
        // Update the recipes state
        setRecipes((prevRecipes) =>
          prevRecipes.map((recipe) =>
            recipe.id === id ? { ...recipe, is_favorited: toLike } : recipe
          )
        );
      })
      .catch((err) => {
        // Enhanced error handling for more informative alerts/logs
        const { errors } = err;
        if (errors) {
          alert(errors.join("\n")); // Display all errors, each on a new line
        } else {
          console.error("Failed to toggle favorite:", err.message || err);
        }
      });
  };
  

  const handleAddToCart = ({ id, toAdd = true, callback }) => {
    const method = toAdd ? api.addToOrders.bind(api) : api.removeFromOrders.bind(api)
    method({ id }).then(res => {
      const recipesUpdated = recipes.map(recipe => {
        if (recipe.id === id) {
          recipe.in_shopping_cart = toAdd
        }
        return recipe
      })
      setRecipes(recipesUpdated)
      callback && callback(toAdd)
    })
    .catch(err => {
      const { errors } = err
      if (errors) {
        alert(errors)
      }
    })
  }

  return {
    recipes,
    setRecipes,
    recipesCount,
    setRecipesCount,
    recipesPage,
    setRecipesPage,
    tagsValue,
    handleLike,
    handleAddToCart,
    handleTagsChange,
    setTagsValue
  }
}
