import React from 'react';
import './css/Navbar.css'; // For Navbar specific styling

const Navbar = () => {
  const handleLogin = () => {
    
  };

  const handleSignup = () => {
    alert('Signup button clicked!');
    // In a real app, you'd navigate to a signup page or open a modal
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <h1>Setu</h1>
      </div>
      <div className="navbar-links">
        {/* You can add more navigation links here if needed */}
        <button onClick={handleLogin} className="navbar-button">Login</button>
        <button onClick={handleSignup} className="navbar-button primary">Sign Up</button>
      </div>
    </nav>
  );
};

export default Navbar;