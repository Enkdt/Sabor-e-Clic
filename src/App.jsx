import { useState, useEffect } from 'react'
import './App.css'
import { Route, Routes } from 'react-router-dom';
import { Home } from './Home';
import { Login } from './Login';
import { SignUp } from './SignUp';
import { AgdBancada } from './AgdBancada';
import { Bancada } from './Bancada';
import { Estoque } from './Estoque';
function App() {
 return (
    <>
    <Routes>
      <Route path='/' element={<Home/>}/>
      <Route path='/login' element={<Login/>}/>
      <Route path='/cadastro' element={<SignUp/>}/>
      <Route path='/AgdBancada' element={<AgdBancada/>}/>
      <Route path='/Bancada' element={<Bancada/>}/>
      <Route path='/Estoque' element={<Estoque/>}/>
    </Routes>
    </>
  )

}

export default App
