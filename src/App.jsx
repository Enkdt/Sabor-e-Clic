import { useState, useEffect } from 'react'
import './App.css'
import { Route, Routes } from 'react-router-dom';
import { Home } from './Home';
import { Login } from './Login';
import { SignUp } from './SignUp';
import { AgdBancada } from './AgdBancada';
import { Bancada } from './Bancada';
import { Estoque } from './Estoque';
import { AdcEstoque } from './AdcEstoque';
import { Carrinho } from './Carrinho';
import { EmailVerification } from './EmailVerification';
function App() {
 return (
    <>
    <Routes>
      <Route path='/' element={<Home/>}/>
      <Route path='/login' element={<Login/>}/>
      <Route path='/cadastro' element={<SignUp/>}/>
      <Route path='/cadastro/autenticar' element={<EmailVerification/>}/>
      <Route path='/AgdBancada' element={<AgdBancada/>}/>
      <Route path='/Bancada' element={<Bancada/>}/>
      <Route path='/Estoque' element={<Estoque/>}/>
      <Route path='/AdcEstoque' element={<AdcEstoque/>}/>
      <Route path='/Carrinho' element={<Carrinho/>}/>
    </Routes>
    </>
  )

}

export default App
