import React, { useState, useEffect } from "react";
import { GeistProvider, CssBaseline, Select} from "@geist-ui/core";
import { Sun, Moon } from "@geist-ui/icons";

const Theme = ({ theme, setTheme }) => {
  // Handler to switch theme on select change
  const handler = (val) => {
    const selectedTheme = val === "1" ? "light" : "dark";
    setTheme(selectedTheme);
    localStorage.setItem("theme", selectedTheme);
    document.documentElement.setAttribute("data-theme", selectedTheme);
  };

  return (
    <Select
      value={theme === "light" ? "1" : "2"}
      onChange={handler}
      className="theme-select"
      pure
      style={{ fontFamily: "'NeueMontreal', sans-serif", fontWeight: "400" }}
    >
      <Select.Option value="1" style={{ fontFamily: "'NeueMontreal', sans-serif", fontWeight: "400" }}>
        <span style={{ display: "flex", alignItems: "center" }}>
          <Sun size={14} />&nbsp;Light
        </span>
      </Select.Option>
      <Select.Option value="2" style={{ fontFamily: "'NeueMontreal', sans-serif", fontWeight: "400" }}>
        <span style={{ display: "flex", alignItems: "center" }}>
          <Moon size={14} />&nbsp;Dark
        </span>
      </Select.Option>
    </Select>
  );
};

const App = () => {
  const [theme, setTheme] = useState("light"); // Default to light

  // Load theme from localStorage when the app starts
  useEffect(() => {
    const savedTheme = localStorage.getItem("theme") || "light";
    setTheme(savedTheme);
    document.documentElement.setAttribute("data-theme", savedTheme);
  }, []);

  return (
    <GeistProvider themeType={theme}>
      <CssBaseline />
      <Theme theme={theme} setTheme={setTheme} />
    </GeistProvider>
  );
};

export default App;