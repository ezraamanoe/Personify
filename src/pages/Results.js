import { CssBaseline, GeistProvider, Card, Button, Divider, Select, Drawer} from '@geist-ui/core';
import React, { useEffect, useState, useRef } from 'react';
import { Typewriter } from 'react-simple-typewriter';
import { Sun, Moon, Github, Linkedin, Menu, Download} from "@geist-ui/icons";
import '../App.css';

const Theme = ({ theme, setTheme }) => {
  const handler = (val) => {
    const selectedTheme = val === "1" ? "light" : "dark";
    setTheme(selectedTheme);
    localStorage.setItem("theme", selectedTheme);
    document.documentElement.setAttribute("data-theme", selectedTheme);
  };

  return (
    <Select value={theme === "light" ? "1" : "2"} onChange={handler} className="custom-select" pure>
      <Select.Option value="1">
        <span style={{ display: "flex", alignItems: "center" }}>
          <Sun size={14} />&nbsp;Light
        </span>
      </Select.Option>
      <Select.Option value="2">
        <span style={{ display: "flex", alignItems: "center" }}>
          <Moon size={14} />&nbsp;Dark
        </span>
      </Select.Option>
    </Select>
  );
};

const Navbar = ({ theme, setTheme }) => {
  const [isDrawerVisible, setDrawerVisible] = useState(false);

  const toggleDrawer = () => setDrawerVisible(!isDrawerVisible);

  return (
      <nav className="navbar">
        <div className="logo">Personify</div>
        <div className="nav-links">
          <a href="https://github.com/ezraamanoe" target="blank" rel="noopener noreferrer">
            <Button auto size="medium" type="abort"><Github size={14}/>&nbsp;GitHub</Button>
          </a>
          <a href="https://www.linkedin.com/in/ezramanoe/" target="blank" rel="noopener noreferrer">
            <Button auto size="medium" type="abort"><Linkedin size={14}/>&nbsp;LinkedIn</Button>
          </a>
          <Theme theme={theme} setTheme={setTheme} />
        </div>

        {/* Hamburger Menu Button */}
        <div className="hamburger" onClick={toggleDrawer}>
          <Menu size={16} />
        </div>

        {/* Drawer Component */}
        <Drawer visible={isDrawerVisible} onClose={toggleDrawer}>
          <div className="drawer-content">
            <a href="https://github.com/ezraamanoe" target="blank" rel="noopener noreferrer">
              <Button auto size="small" type="abort"><Github size={12}/>&nbsp;GitHub</Button>
            </a>
            <a href="https://www.linkedin.com/in/ezramanoe/" target="blank" rel="noopener noreferrer">
              <Button auto size="small" type="abort"><Linkedin size={12}/>&nbsp;LinkedIn</Button>
            </a>
            {/* Theme Toggle Inside Drawer */}
            <Theme theme={theme} setTheme={setTheme} />
          </div>
        </Drawer>
      </nav>
  );
};

const processParagraph = (text) => {
  const segments = text.split(/(\*\*.*?\*\*|\*.*?\*)/g)
    .filter(chunk => chunk)
    .map(chunk => ({
      text: chunk.replace(/\*\*/g, '').replace(/\*/g, ''),
      bold: /\*\*/.test(chunk),
      italic: /\*/.test(chunk) && !/\*\*/.test(chunk)
    }));
  
  return segments.reduce((acc, segment) => {
    if (acc.length > 0 && 
        acc[acc.length-1].bold === segment.bold && 
        acc[acc.length-1].italic === segment.italic) {
      acc[acc.length-1].text += segment.text;
    } else {
      acc.push(segment);
    }
    return acc;
  }, []);
};

const Results = ({ theme }) => {
  const [critique, setCritique] = useState('');
  const [loading, setLoading] = useState(true);
  const [paragraphs, setParagraphs] = useState([]);
  const [currentParaIndex, setCurrentParaIndex] = useState(0);
  const [currentCharIndex, setCurrentCharIndex] = useState(0);
  const intervalRef = useRef(null);
  const isMounted = useRef(true);

  // Fetch critique from API
  useEffect(() => {
    const fetchCritique = async () => {
      try {
        const response = await fetch('https://personify-ai.onrender.com/get-critique', {
          credentials: 'include'  // Essential fix for session cookies
        });
        
        if (!response.ok) throw new Error('Failed to load critique');
        
        const data = await response.json();
        if (isMounted.current) setCritique(data.critique);
      } catch (error) {
        if (isMounted.current) setCritique('Failed to load critique. Please refresh.');
      } finally {
        if (isMounted.current) setLoading(false);
      }
    };
    
    fetchCritique();
    
    return () => {
      isMounted.current = false;
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const downloadImage = () => {
    fetch('https://personify-ai.onrender.com/get-image', {
      credentials: 'include'  // Essential fix for session cookies
    })
      .then((response) => {
        if (!response.ok) throw new Error('Image not ready');
        return response.blob();
      })
      .then((blob) => {
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "critique.png";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      })
      .catch((error) => {
        console.error('Download error:', error);
      });
  };

  // Process critique into paragraphs with styled characters
  useEffect(() => {
    if (!loading && critique) {
      const rawParagraphs = critique.split('\n').filter(p => p.trim() !== '');
      const processedParagraphs = rawParagraphs.map(processParagraph);
      setParagraphs(processedParagraphs);
    }
  }, [loading, critique]);

  // Typing effect for current paragraph
  useEffect(() => {
    if (paragraphs.length === 0 || currentParaIndex >= paragraphs.length) return;

    const currentParagraph = paragraphs[currentParaIndex];
    intervalRef.current = setInterval(() => {
      setCurrentCharIndex(prev => {
        if (prev < currentParagraph.length) return prev + 1;
        
        clearInterval(intervalRef.current);
        setTimeout(() => {
          setCurrentParaIndex(prev => prev + 1);
          setCurrentCharIndex(0);
        }, 1000);
        
        return prev;
      });
    }, 20);

    return () => clearInterval(intervalRef.current);
  }, [currentParaIndex, paragraphs]);

  const currentText = paragraphs[currentParaIndex]?.slice(0, currentCharIndex) || [];

  return (
    <>
      {loading ? (
        <header className='Analyze-header'>
          <span className="analyzing">
            <Typewriter
              words={['Analyzing...', 'Looking through your songs...', 'Almost there...']}
              loop
              cursor
              cursorStyle='|'
              typeSpeed={50}
              deleteSpeed={50}
              delaySpeed={2000}
            />
          </span>
        </header>
      ) : (
      <div className='results-container'>
        <Card>
          <Card.Content my={0}>
            <Button auto iconRight={<Download />} onClick={downloadImage} px={0.6}></Button>
          </Card.Content>
        <Divider h="1px" my={0} />
        <Card.Content>
          {paragraphs.slice(0, currentParaIndex).map((para, i) => (
            <p key={i} style={{color: i === paragraphs.length - 1 ? '#0070F3' : 'inherit'}}>
              {para.map(({ text, bold, italic }, j) => (
                <span
                  key={j}
                  style={{
                    fontWeight: bold ? 'bold' : 'normal',
                    fontStyle: italic ? 'italic' : 'normal',
                  }}
                >
                  {text}
                </span>
              ))}
            </p>
          ))}
          {currentText.length > 0 && (
            <p style={{color: currentParaIndex === paragraphs.length - 1 ? '#0070F3' : 'inherit'}}>
              {currentText.map(({ text, bold, italic }, j) => (
                <span
                  key={j}
                  style={{
                    fontWeight: bold ? 'bold' : 'normal',
                    fontStyle: italic ? 'italic' : 'normal',
                  }}
                >
                  {text}
                </span>
              ))}
            </p>
          )}
        </Card.Content>
        </Card>
        </div>
      )} 
    <footer className="App-footer">
        <p>
          <span className="author">Developed by Ezra Manoe, heavily inspired by <a href="https://pudding.cool/2021/10/judge-my-music/" target="blank" rel="noopener noreferrer">pudding.cool</a></span>
        </p>
    </footer>
    </>
  );
};

const App = () => {
  const [theme, setTheme] = useState("light");

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme") || "light";
    setTheme(savedTheme);
    document.documentElement.setAttribute("data-theme", savedTheme);
  }, []);

  return (
    <GeistProvider themeType={theme}>
      <CssBaseline />
      <div className='App'>
      <Navbar theme={theme} setTheme={setTheme} />
      <Results theme={theme} setTheme={setTheme} />
      </div>
    </GeistProvider>
  );
};

export default App;