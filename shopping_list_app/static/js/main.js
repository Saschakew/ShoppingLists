// Main JavaScript file for the Shopping List App

// Define grocery categories and associated keywords
const groceryCategories = {
  "Fruits": ["apple", "banana", "orange", "berries", "grape", "mango", "pineapple", "avocado", "peach", "plum"],
  "Vegetables": ["carrot", "broccoli", "spinach", "onion", "garlic", "potato", "tomato", "lettuce", "cabbage", "pepper", "cucumber", "zucchini", "celery"],
  "Dairy": ["milk", "cheese", "yogurt", "butter", "cream", "sour cream", "cottage cheese"],
  "Bakery": ["bread", "rolls", "bagel", "croissant", "muffin", "cake", "donuts", "cookies", "pie"],
  "Meat & Poultry": ["chicken", "beef", "pork", "turkey", "sausage", "bacon", "lamb", "ham"],
  "Fish & Seafood": ["salmon", "tuna", "shrimp", "cod", "tilapia", "crab", "lobster"],
  "Pantry Staples": ["pasta", "rice", "flour", "sugar", "oil", "vinegar", "spices", "herbs", "canned goods", "beans", "lentils", "cereal", "oats", "jam", "honey", "peanut butter", "nuts", "seeds", "broth", "soup"],
  "Frozen Foods": ["ice cream", "frozen vegetables", "frozen fruit", "frozen meals", "pizza", "fries"],
  "Beverages": ["water", "juice", "soda", "tea", "coffee", "milkshake", "sports drink", "beer", "wine"], // Note: 'milk' is also in Dairy, consider context or prioritize
  "Household": ["toilet paper", "paper towels", "soap", "shampoo", "detergent", "cleaning supplies", "trash bags", "foil", "plastic wrap"],
  "Other": [] // Fallback category
};

// Function to determine category (will be implemented in a later step)
function determineCategory(itemName) {
  const lowerItemName = itemName.toLowerCase();
  for (const category in groceryCategories) {
    if (category === "Other") continue; // Skip 'Other' for keyword matching
    for (const keyword of groceryCategories[category]) {
      if (lowerItemName.includes(keyword.toLowerCase())) { // ensure keyword is also lowercased for comparison
        return category;
      }
    }
  }
  return "Other"; // Default if no keywords match
}


document.addEventListener('DOMContentLoaded', function() {
    console.log('Shopping List App JS Loaded');
    console.log('Grocery categories defined:', groceryCategories);

    // Example: Add event listeners or client-side logic here
    // e.g., for handling form submissions via Fetch API, DOM manipulations etc.
});
