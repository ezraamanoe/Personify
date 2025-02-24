import React, { useState, useEffect } from "react";
import './App.css';
import { GeistProvider, CssBaseline} from '@geist-ui/core';
import { BrowserRouter as Router, Routes, Route} from 'react-router-dom';
import Home from './pages/Home';
import Results from './pages/Results'

const App = () => {
  const [theme, setTheme] = useState("light");

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme") || "light";
    setTheme(savedTheme);
    document.documentElement.setAttribute("data-theme", savedTheme);
  }, []);

  return (
    <GeistProvider theme={theme}>
      <CssBaseline>
    <Router>
      <Routes>
        <Route path="/" element={<Home theme={theme} setTheme={setTheme}/>} /> 
        <Route path="/results" element={<Results theme={theme} setTheme={setTheme}/>} />
      </Routes>
    </Router>
    </CssBaseline>
    </GeistProvider>
  );
}

export default App;