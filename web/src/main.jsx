import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { BrowserRouter } from 'react-router-dom'
import { applyThemePreference, readPreference } from './themeContext.js'

// Aplica o tema antes da primeira pintura para evitar flash.
applyThemePreference(readPreference())

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
        <App/>
    </BrowserRouter>
  </StrictMode>,
)
