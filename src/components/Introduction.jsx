import React from 'react';
import './css/Introduction.css'; // For Introduction specific styling

const Introduction = () => {
  return (
    <section className="introduction">
      <div className="intro-content ">
        <h2 className='text-blue-600'>Setu: Safe Internet</h2>
        <p>
          Setu: Safe Internet is an AI-driven safety solution that identifies age-appropriate content by analyzing children's web searches and linking them to peer-reviewed research. It explains, allows, or blocks results and provides parents with a monitoring dashboard to oversee online activity in real time.
        </p>
              <button
        className="btn"
      >
        Go to Dashboard
      </button>
      </div>
    </section>
  );
};

export default Introduction;