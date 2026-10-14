import { useState, useEffect } from 'react'
import './App.css'
import { Route, Routes } from 'react-router-dom';
import { Home } from './Home';
import { Login } from './Login';
function App() {

  const [currentTime,setCurrentTime] = useState(0);
  
  // 2 param é dependency

  //Comentei só pra tirar da tela por enquanto :p
  //useEffect(()=>{
  //  fetch('/api/time')
  //  .then(res => res.json())
  //  .then(data => {
  //    setCurrentTime(data.time);
  //  });
  //},[]);

  //{currentTime ? (
  //      <p>Teste da api {new Date(currentTime * 1000).toLocaleString('pt-BR')}</p>
  //      ) : (
  //          <p>Carregando horário do servidor Flask...</p>
  //      )}      

  return (
    <>
    <Routes>
      <Route path='/' element={<Home/>}/>
      <Route path='/login' element={<Login/>}/>
    </Routes>
    </>
  )

}

export default App
