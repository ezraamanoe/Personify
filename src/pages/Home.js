import React, { useEffect, useState} from 'react';
import '../App.css';
import { GeistProvider, CssBaseline, Button} from '@geist-ui/core';
import { Typewriter } from 'react-simple-typewriter';
import Navbar from '../components/Navbar';

const Home = ({ theme }) => {
  const handleSpotifyAuth = async () => {
    try {
        window.location.href = "http://personify-nu.vercel.app/login";
    } catch (error) {
        console.error("Error during authentication:", error);
    }
};

    return (
      <>
        <div className="App">
            <Navbar/>
            <header className="App-header">
                <p>
                    <span className="Description">Let A.I. judge your atrocious taste in music and guess your personality type.</span>
                <br />
                <br />
                    <span className="Quotes">
                        <Typewriter
                          words={['"is that from tiktok?"', 
                                  '"esoteric niche snob"', 
                                  '"divorced dad core"',
                                  '"performative taste"']}
                          loop
                          cursor
                          cursorStyle='|'
                          typeSpeed={50}
                          deleteSpeed={50}
                          delaySpeed={3000}
                        />
                    </span>
                </p>
                <br />
                <Button type="success" aria-label="Find Out" auto scale={1.5} onClick={handleSpotifyAuth}>
                    <span>Find Out</span>
                </Button>
            </header>
            <footer className="App-footer">
                 <p>
                    <span className="author">Developed by Ezra Manoe, heavily inspired by <a href="https://pudding.cool/2021/10/judge-my-music/" target="blank">pudding.cool</a></span>
                </p>
            </footer>
        </div>
  
          
      </>
    );
  }

  const App = () => {
    const [theme, setTheme] = useState("light");
    useEffect(() => {
      const savedTheme = localStorage.getItem("theme") || "light";
      setTheme(savedTheme);
      document.documentElement.setAttribute("data-theme", savedTheme);
    }, []);
  
    return (
      <GeistProvider theme={theme}>
        <CssBaseline />
        <Home theme={theme} setTheme={setTheme} />
      </GeistProvider>
    );
  };
  
  export default App;