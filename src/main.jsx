import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { BrowserRouter } from 'react-router-dom'

const initialTheme = localStorage.getItem('theme-preference') || 'system'
document.documentElement.dataset.theme = initialTheme
document.documentElement.style.colorScheme = initialTheme === 'system' ? '' : initialTheme

import 'animate.css';
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
        <App/>
    </BrowserRouter>
  </StrictMode>,
)
