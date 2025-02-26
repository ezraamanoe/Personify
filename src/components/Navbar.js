import React, { useState, useEffect } from "react";
import { GeistProvider, CssBaseline, Button, Drawer, Select } from "@geist-ui/core";
import { Sun, Moon, Github, Linkedin, Menu } from "@geist-ui/icons";

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

const goHome = () => {
  window.location.href = 'https://personify-ai.onrender.com'; 
};

const Navbar = ({ theme, setTheme }) => {
  const [isDrawerVisible, setDrawerVisible] = useState(false);

  const toggleDrawer = () => setDrawerVisible(!isDrawerVisible);

  return (
    <>
      <nav className="navbar">
        <div className="logo" onClick={goHome}>
          Personify
        </div>
        <div className="nav-links">
          <a href="https://github.com/ezraamanoe" target="blank" rel="noopener noreferrer">
            <Button auto size="medium" type="abort"><Github size={14}/>&nbsp;GitHub</Button>
          </a>
          <a href="https://www.linkedin.com/in/ezramanoe/" target="blank" rel="noopener noreferrer">
            <Button auto size="medium" type="abort"><Linkedin size={14}/>&nbsp;LinkedIn</Button>
          </a>
          <Theme theme={theme} setTheme={setTheme} />
        </div>

        <div className="hamburger" onClick={toggleDrawer}>
          <Menu size={16} />
        </div>

        <Drawer visible={isDrawerVisible} onClose={toggleDrawer}>
          <div className="drawer-content">
            <a href="https://github.com/ezraamanoe" target="blank" rel="noopener noreferrer">
              <Button auto size="small" type="abort"><Github size={12}/>&nbsp;GitHub</Button>
            </a>
            <a href="https://www.linkedin.com/in/ezramanoe/" target="blank" rel="noopener noreferrer">
              <Button auto size="small" type="abort"><Linkedin size={12}/>&nbsp;LinkedIn</Button>
            </a>
            <Theme theme={theme} setTheme={setTheme} />
          </div>
        </Drawer>
      </nav>
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
      <Navbar theme={theme} setTheme={setTheme} />
    </GeistProvider>
  );
};

export default App;
