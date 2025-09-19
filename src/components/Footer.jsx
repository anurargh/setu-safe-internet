import React from 'react';
import './css/footer.css'; // For Footer specific styling

const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-content">
        <p>&copy; {new Date().getFullYear()} Setu: Safe Internet. All rights reserved.</p>
        <div className="footer-links">
          {/* Add any relevant footer links here */}
          <a href="/privacy">Privacy Policy</a>
          <a href="/terms">Terms of Service</a>
          <a href="/contact">Contact Us</a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;