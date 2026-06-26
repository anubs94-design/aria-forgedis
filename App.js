// App.js
// Point d'entree de l'application. Affiche l'ecran principal.
// (L'ancien code complet a ete porte vers src/screens/MainScreen.js
// et src/services/WebSocketService.js + AudioService.js)

import React from "react";
import MainScreen from "./src/screens/MainScreen";

export default function App() {
  return <MainScreen />;
}