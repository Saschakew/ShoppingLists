// Main JavaScript file for the Shopping List App

// Define grocery categories and associated keywords
const groceryCategories = {
  "Fruits": ["apple", "apfel", "banana", "banane", "orange", "beeren", "berries", "grape", "traube", "mango", "pineapple", "ananas", "avocado", "peach", "pfirsich", "plum", "pflaume", "strawberry", "erdbeere", "raspberry", "himbeere", "blueberry", "blaubeere", "heidelbeere", "kiwi", "lemon", "zitrone", "lime", "limette"],
  "Vegetables": ["carrot", "karotte", "möhre", "broccoli", "brokkoli", "spinach", "spinat", "onion", "zwiebel", "garlic", "knoblauch", "potato", "kartoffel", "tomato", "tomate", "lettuce", "salat", "kopfsalat", "cabbage", "kohl", "pepper", "paprika", "cucumber", "gurke", "zucchini", "celery", "sellerie", "corn", "mais", "mushroom", "pilz", "champignon", "pea", "erbse", "green beans", "grüne bohnen"],
  "Dairy": ["milk", "milch", "cheese", "käse", "yogurt", "joghurt", "butter", "cream", "sahne", "quark", "sour cream", "saure sahne", "schmand", "cottage cheese", "hüttenkäse", "körniger frischkäse"],
  "Bakery": ["bread", "brot", "rolls", "brötchen", "bagel", "croissant", "muffin", "cake", "kuchen", "donuts", "donut", "cookies", "kekse", "plätzchen", "pie", "obstkuchen"],
  "Meat & Poultry": ["chicken", "huhn", "hähnchen", "beef", "rindfleisch", "pork", "schweinefleisch", "turkey", "pute", "putenfleisch", "sausage", "wurst", "würstchen", "bacon", "speck", "lamb", "lamm", "lammfleisch", "ham", "schinken", "mince", "hackfleisch", "ground meat"],
  "Fish & Seafood": ["salmon", "lachs", "tuna", "thunfisch", "shrimp", "garnele", "krabbe", "cod", "kabeljau", "dorsch", "tilapia", "crab", "krebs", "lobster", "hummer", "herring", "hering", "trout", "forelle"],
  "Pantry Staples": ["pasta", "nudeln", "rice", "reis", "flour", "mehl", "sugar", "zucker", "oil", "öl", "vinegar", "essig", "spices", "gewürze", "herbs", "kräuter", "canned goods", "konserven", "dosenware", "beans", "bohnen", "lentils", "linsen", "cereal", "müsli", "cornflakes", "getreideflocken", "oats", "haferflocken", "jam", "marmelade", "honey", "honig", "peanut butter", "erdnussbutter", "nuts", "nüsse", "seeds", "samen", "kerne", "broth", "brühe", "soup", "suppe", "chocolate", "schokolade", "ketchup", "mustard", "senf", "mayonnaise", "mayo"],
  "Frozen Foods": ["ice cream", "eis", "eiscreme", "frozen vegetables", "tiefkühlgemüse", "tk-gemüse", "frozen fruit", "tiefkühlobst", "tk-obst", "frozen meals", "fertiggerichte", "tk-fertiggerichte", "pizza", "tiefkühlpizza", "tk-pizza", "fries", "pommes", "frozen fish", "tk-fisch"],
  "Beverages": ["water", "wasser", "juice", "saft", "soda", "limo", "limonade", "tea", "tee", "coffee", "kaffee", "milkshake", "milchshake", "sports drink", "sportgetränk", "isodrink", "beer", "bier", "wine", "wein", "cola"],
  "Household": ["toilet paper", "toilettenpapier", "klopapier", "paper towels", "küchenrolle", "papiertücher", "soap", "seife", "shampoo", "detergent", "waschmittel", "spülmittel", "cleaning supplies", "putzmittel", "reinigungsmittel", "trash bags", "müllbeutel", "foil", "alufolie", "plastic wrap", "frischhaltefolie", "batteries", "batterien", "light bulb", "glühbirne"],
  "Other": [] // Fallback category
};

// Function to determine category
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
