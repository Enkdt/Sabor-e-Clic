import { useState, useEffect } from 'react'
import './App.css'
import { Route, Routes } from 'react-router-dom';
import { Home } from './Home';
import { Login } from './Login';
import { SignUp } from './SignUp';
import { Restaurant } from './Restaurant';
import { Dish } from './Dish';
import { Order } from './Order';
import { Profile } from './Profile';
import { Stock } from './Manager/Stock';
import { StockAdd } from './Manager/StockAdd';
import { Dashboard } from './Manager/Dashboard';
function App() {
 return (
    <>
    <Routes>
      <Route path='/' element={<Home/>}/>
      <Route path='/login' element={<Login/>}/>
      <Route path='/cadastro' element={<SignUp/>}/>
      <Route path='/restaurante/:id' element={<Restaurant/>}/>
      <Route path='/prato/:id' element={<Dish/>}/>
      <Route path='/pedido' element={<Order/>}/>
      <Route path='/perfil' element={<Profile/>}/>
      <Route path='/gerente/estoque' element={<Stock/>}/>
      <Route path='/gerente/estoque/adicionar' element={<StockAdd/>}/>
      <Route path='/gerente/dashboard' element={<Dashboard/>}/>
    </Routes>
    </>
  )

}

export default App
