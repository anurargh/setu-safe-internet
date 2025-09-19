import React from 'react';
import Navbar from './components/Navbar';
import Introduction from './components/Introduction';
import Footer from './components/Footer';
import './App.css'; // For basic styling

function App() {
  return (
    <div className="App">
      <Navbar />
      <Introduction />
      <Footer />
    </div>
  );
}

export default App;